from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models import Booking, Test, TestCategory, Report
from extensions import db
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


@patient.route('/book-test', methods=['GET', 'POST'])
@role_required('patient')
def book_test():

    categories = TestCategory.query.all()
    tests = Test.query.filter_by(is_active=True).order_by(Test.name).all()

    if request.method == 'POST':

        test_id = request.form.get('test_id')
        booking_date_str = request.form.get('booking_date')
        slot_time = request.form.get('slot_time')
        home_collection = request.form.get('home_collection') == 'on'
        collection_address = request.form.get('collection_address', '').strip()

        if not all([test_id, booking_date_str, slot_time]):
            flash('Please fill in all required fields.', 'error')
            return render_template('patient/book_test.html', categories=categories, tests=tests)

        test = Test.query.get(test_id)
        if not test:
            flash('Invalid test selected.', 'error')
            return render_template('patient/book_test.html', categories=categories, tests=tests)

        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('patient/book_test.html', categories=categories, tests=tests)

        if booking_date < datetime.today().date():
            flash('Cannot book for a past date.', 'error')
            return render_template('patient/book_test.html', categories=categories, tests=tests)

        booking = Booking(
            user_id=current_user.id,
            test_id=test.id,
            booking_date=booking_date,
            slot_time=slot_time,
            home_collection=home_collection,
            collection_address=collection_address if home_collection else ''
        )

        db.session.add(booking)
        db.session.commit()

        flash('Test booked successfully! We will confirm your appointment soon. ✅', 'success')
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
