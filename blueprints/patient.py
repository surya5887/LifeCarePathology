from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user
from flask_mail import Message
from models import Booking, Test, TestCategory, Report, BlockedSlot
from extensions import db, mail
from datetime import datetime
from utils import role_required

patient = Blueprint('patient', __name__, url_prefix='/patient')


@patient.route('/dashboard')
@role_required('patient')
def dashboard():

    user_bookings = Booking.query.filter_by(user_id=current_user.id)

    upcoming_bookings = user_bookings.filter(
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.booking_date.desc()).limit(5).all()

    total_bookings = user_bookings.count()
    completed = user_bookings.filter_by(status='completed').count()
    pending = user_bookings.filter_by(status='pending').count()

    # Get reports for this patient (by name match)
    user_reports = Report.query.filter(
        Report.patient_name.ilike(f'%{current_user.name}%')
    ).order_by(Report.uploaded_at.desc()).all()

    return render_template(
        'patient/dashboard.html',
        upcoming_bookings=upcoming_bookings,
        total_bookings=total_bookings,
        completed=completed,
        pending=pending,
        user_reports=user_reports
    )


@patient.route('/api/check-availability')
@role_required('patient')
def check_availability():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date required'}), 400

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    # Check full day block
    full_block = BlockedSlot.query.filter_by(date=date_obj, time_slot=None).first()
    if full_block:
        return jsonify({'full_day_blocked': True, 'reason': full_block.reason})

    # Available slots (Standard 7 AM - 8 PM)
    all_slots = [
        "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
        "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM", "06:00 PM",
        "07:00 PM", "08:00 PM"
    ]

    # Get blocked slots for this date
    blocked_db = BlockedSlot.query.filter(
        BlockedSlot.date == date_obj,
        BlockedSlot.time_slot.isnot(None)
    ).all()
    blocked_times = {b.time_slot for b in blocked_db}

    # Optional: Check existing bookings if you want to limit slots (e.g. 1 per slot)
    # booked_db = Booking.query.filter_by(booking_date=date_obj, status='confirmed').all()
    # booked_times = {b.slot_time for b in booked_db}
    # blocked_times.update(booked_times)

    response_slots = []
    for slot in all_slots:
        response_slots.append({
            'time': slot,
            'is_blocked': slot in blocked_times
        })

    return jsonify({'full_day_blocked': False, 'slots': response_slots})


@patient.route('/book-test', methods=['GET', 'POST'])
@role_required('patient')
def book_test():
    categories = TestCategory.query.all()
    tests = Test.query.filter_by(is_active=True).order_by(Test.name).all()

    if request.method == 'POST':
        test_id = request.form.get('test_id')
        booking_date_str = request.form.get('booking_date')
        slot_time = request.form.get('slot_time')
        
        # New Fields
        patient_name = request.form.get('patient_name')
        patient_phone = request.form.get('patient_phone')
        patient_email = request.form.get('patient_email')
        patient_address = request.form.get('patient_address')
        referral_type = request.form.get('referral_type', 'self')
        referral_doctor = request.form.get('referral_doctor') if referral_type == 'doctor' else 'Self'
        home_collection = request.form.get('home_collection') == 'on'

        if not all([test_id, booking_date_str, slot_time, patient_name, patient_phone, patient_address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('patient/book_test.html', categories=categories, tests=tests)

        test = Test.query.get(test_id)
        if not test:
            flash('Invalid test selected.', 'error')
            return redirect(url_for('patient.book_test'))

        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('patient.book_test'))

        if booking_date < datetime.today().date():
            flash('Cannot book for a past date.', 'error')
            return redirect(url_for('patient.book_test'))

        # Check availability again server-side
        if BlockedSlot.query.filter(
            (BlockedSlot.date == booking_date) & 
            ((BlockedSlot.time_slot == slot_time) | (BlockedSlot.time_slot == None))
        ).first():
            flash('Selected slot is unavailable. Please choose another.', 'error')
            return redirect(url_for('patient.book_test'))

        booking = Booking(
            user_id=current_user.id,
            test_id=test.id,
            booking_date=booking_date,
            slot_time=slot_time,
            
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=patient_email,
            patient_address=patient_address,
            referral_type=referral_type,
            referral_doctor=referral_doctor,
            payment_mode='Offline',
            
            home_collection=home_collection,
            collection_address=patient_address if home_collection else ''
        )

        db.session.add(booking)
        db.session.commit()

        # ── Send Email Notifications ──
        try:
            # 1. Email to Patient
            if patient_email:
                msg = Message(f'Booking Confirmed - {test.name}',
                              recipients=[patient_email])
                msg.body = f"""Dear {patient_name},

Your appointment for {test.name} has been booked successfully.

Date: {booking_date_str}
Time: {slot_time}
Location: {'Home Collection' if home_collection else 'Lab Visit'}
Address: {patient_address}

Please pay ₹{test.price} at the time of collection/visit.

Thank you,
Life Care Pathology Lab
                """
                mail.send(msg)

            # 2. Email to Admin (Default Sender)
            admin_msg = Message(f'New Booking: {test.name}',
                                recipients=[current_app.config.get('MAIL_USERNAME')])
            admin_msg.body = f"""New Booking Received!

Patient: {patient_name} ({patient_phone})
Test: {test.name}
Date: {booking_date_str} | Time: {slot_time}
Type: {'Home Collection' if home_collection else 'Lab Visit'}
            """
            mail.send(admin_msg)
        except Exception as e:
            print(f"Email Error: {e}")
            # Don't rollback booking if email fails, just log it.

        flash('Test booked successfully! Confirmation email sent. ✅', 'success')
        return redirect(url_for('patient.my_bookings'))

    return render_template('patient/book_test.html', categories=categories, tests=tests)


@patient.route('/my-bookings')
@role_required('patient')
def my_bookings():

    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.created_at.desc()
    ).all()

    return render_template('patient/my_bookings.html', bookings=bookings)


@patient.route('/profile', methods=['GET', 'POST'])
@role_required('patient')
def profile():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if name:
            current_user.name = name
        if phone:
            current_user.phone = phone

        current_user.address = address

        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return render_template('patient/profile.html')
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully! ✅', 'success')
        return redirect(url_for('patient.profile'))

    return render_template('patient/profile.html')
