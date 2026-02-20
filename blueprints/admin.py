import os
import csv
import io
import json
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, Response, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (User, Test, TestCategory, Booking, Report,
                    ContactEnquiry, Testimonial, DoctorReferral,
                    ActivityLog, SiteSettings, TestParameter, ReportTemplate, BlockedSlot)
from extensions import db
from utils import role_required
from file_utils import validate_pdf
from report_generator import generate_report_pdf
from sqlalchemy import func

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.before_request
@login_required
def before_request():
    pass


def log_activity(action, details=''):
    """Helper to log admin activity."""
    log = ActivityLog(admin_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()


# ═══════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════
@admin.route('/dashboard')
@role_required('admin')
def dashboard():
    total_patients = User.query.filter_by(role='patient').count()
    total_tests = Test.query.count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    total_reports = Report.query.count()
    unread_enquiries = ContactEnquiry.query.filter_by(is_read=False).count()

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()

    # Revenue (completed bookings)
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    monthly_revenue = db.session.query(func.sum(Test.price)).join(
        Booking, Booking.test_id == Test.id
    ).filter(
        Booking.status == 'completed',
        Booking.booking_date >= month_start
    ).scalar() or 0

    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           total_tests=total_tests,
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           total_reports=total_reports,
                           unread_enquiries=unread_enquiries,
                           recent_bookings=recent_bookings,
                           monthly_revenue=monthly_revenue)


# ═══════════════════════════════════════════════════════
#  TEST MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/tests')
@role_required('admin')
def tests():
    all_tests = Test.query.order_by(Test.created_at.desc()).all()
    return render_template('admin/tests.html', tests=all_tests)


@admin.route('/tests/add', methods=['GET', 'POST'])
@role_required('admin')
def add_test():
    categories = TestCategory.query.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        description = request.form.get('description', '').strip()
        sample_type = request.form.get('sample_type', 'Blood').strip()
        report_time = request.form.get('report_time', '24 Hours').strip()

        if not all([name, category_id, price]):
            flash('Please fill in all required fields.', 'error')
            return render_template('admin/test_form.html', categories=categories, test=None)

        test = Test(name=name, category_id=int(category_id), price=float(price),
                    description=description, sample_type=sample_type, report_time=report_time)
        db.session.add(test)
        db.session.commit()
        log_activity('Added test', f'Test: {name}')
        flash(f'Test "{name}" added successfully! ✅', 'success')
        return redirect(url_for('admin.tests'))

    return render_template('admin/test_form.html', categories=categories, test=None)


@admin.route('/tests/edit/<int:test_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)
    categories = TestCategory.query.all()

    if request.method == 'POST':
        test.name = request.form.get('name', '').strip()
        test.category_id = int(request.form.get('category_id'))
        test.price = float(request.form.get('price'))
        test.description = request.form.get('description', '').strip()
        test.sample_type = request.form.get('sample_type', 'Blood').strip()
        test.report_time = request.form.get('report_time', '24 Hours').strip()
        test.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        log_activity('Updated test', f'Test: {test.name}')
        flash(f'Test "{test.name}" updated successfully! ✅', 'success')
        return redirect(url_for('admin.tests'))

    return render_template('admin/test_form.html', categories=categories, test=test)


@admin.route('/tests/delete/<int:test_id>', methods=['POST'])
@role_required('admin')
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    name = test.name
    db.session.delete(test)
    db.session.commit()
    log_activity('Deleted test', f'Test: {name}')
    flash(f'Test "{name}" deleted. 🗑️', 'success')
    return redirect(url_for('admin.tests'))


# ═══════════════════════════════════════════════════════
#  CATEGORY MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/categories')
@role_required('admin')
def categories():
    all_categories = TestCategory.query.all()
    return render_template('admin/categories.html', categories=all_categories)


@admin.route('/categories/add', methods=['GET', 'POST'])
@role_required('admin')
def add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        icon = request.form.get('icon', '🧪').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Category name is required.', 'error')
            return render_template('admin/category_form.html', category=None)

        cat = TestCategory(name=name, icon=icon, description=description)
        db.session.add(cat)
        db.session.commit()
        log_activity('Added category', f'Category: {name}')
        flash(f'Category "{name}" added! ✅', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/category_form.html', category=None)


@admin.route('/categories/edit/<int:cat_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_category(cat_id):
    cat = TestCategory.query.get_or_404(cat_id)

    if request.method == 'POST':
        cat.name = request.form.get('name', '').strip()
        cat.icon = request.form.get('icon', '🧪').strip()
        cat.description = request.form.get('description', '').strip()
        db.session.commit()
        log_activity('Updated category', f'Category: {cat.name}')
        flash(f'Category "{cat.name}" updated! ✅', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/category_form.html', category=cat)


@admin.route('/categories/delete/<int:cat_id>', methods=['POST'])
@role_required('admin')
def delete_category(cat_id):
    cat = TestCategory.query.get_or_404(cat_id)
    if cat.tests:
        flash('Cannot delete category with existing tests. Remove tests first.', 'error')
        return redirect(url_for('admin.categories'))
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    log_activity('Deleted category', f'Category: {name}')
    flash(f'Category "{name}" deleted. 🗑️', 'success')
    return redirect(url_for('admin.categories'))


# ═══════════════════════════════════════════════════════
#  AVAILABILITY MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/availability', methods=['GET', 'POST'])
@role_required('admin')
def availability():
    if request.method == 'POST':
        date_str = request.form.get('date')
        time_slot = request.form.get('time_slot')
        reason = request.form.get('reason', 'Unavailable')

        if not date_str:
            flash('Date is required.', 'error')
            return redirect(url_for('admin.availability'))

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            if time_slot == 'all':
                time_slot = None  # Block entire day
            
            # Check duplicate
            exists = BlockedSlot.query.filter_by(date=date_obj, time_slot=time_slot).first()
            if exists:
                flash('This slot/date is already blocked.', 'error')
            else:
                block = BlockedSlot(date=date_obj, time_slot=time_slot, reason=reason)
                db.session.add(block)
                db.session.commit()
                log_activity('Blocked availability', f'Date: {date_str}, Slot: {time_slot or "Full Day"}')
                flash('Availability blocked successfully. ✅', 'success')
        except ValueError:
            flash('Invalid date format.', 'error')

        return redirect(url_for('admin.availability'))

    # GET: Show upcoming blocked slots
    today = datetime.utcnow().date()
    blocked_slots = BlockedSlot.query.filter(BlockedSlot.date >= today)\
        .order_by(BlockedSlot.date, BlockedSlot.time_slot).all()
    
    return render_template('admin/availability.html', blocked_slots=blocked_slots, today=today)


@admin.route('/availability/<int:block_id>/delete', methods=['POST'])
@role_required('admin')
def delete_blocked_slot(block_id):
    block = BlockedSlot.query.get_or_404(block_id)
    db.session.delete(block)
    db.session.commit()
    log_activity('Unblocked availability', f'Date: {block.date}, Slot: {block.time_slot}')
    flash('Slot unblocked successfully. ✅', 'success')
    return redirect(url_for('admin.availability'))


# ═══════════════════════════════════════════════════════
#  APPOINTMENTS / BOOKINGS
# ═══════════════════════════════════════════════════════
@admin.route('/appointments')
@role_required('admin')
def appointments():
    status_filter = request.args.get('status', '')
    query = Booking.query.order_by(Booking.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    bookings = query.all()
    return render_template('admin/appointments.html', bookings=bookings, status_filter=status_filter)


@admin.route('/appointments/<int:booking_id>/update', methods=['POST'])
@role_required('admin')
def update_appointment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        booking.status = new_status
        if new_status == 'confirmed':
            booking.payment_status = 'paid'
        db.session.commit()
        log_activity('Updated booking status', f'Booking #{booking.id} → {new_status}')
        flash(f'Booking #{booking.id} status updated to {new_status}. ✅', 'success')
    return redirect(url_for('admin.appointments'))


@admin.route('/appointments/<int:booking_id>/delete', methods=['POST'])
@role_required('admin')
def delete_appointment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    log_activity('Deleted booking', f'Booking #{booking_id}')
    flash(f'Booking #{booking_id} deleted. 🗑️', 'success')
    return redirect(url_for('admin.appointments'))


# ═══════════════════════════════════════════════════════
#  REPORT MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/upload-report', methods=['GET', 'POST'])
@role_required('admin')
def upload_report():
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        token_number = request.form.get('token_number', '').strip()
        password = request.form.get('password')
        remarks = request.form.get('remarks')
        file = request.files.get('report_file')

        if not all([patient_name, password, file]):
            flash('Please fill all required fields and select a PDF file.', 'error')
            return render_template('admin/upload_report.html')

        is_valid, error_msg = validate_pdf(file)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('admin/upload_report.html')

        report_id = Report.generate_report_id()
        if not token_number:
            token_number = report_id

        filename = secure_filename(f"{report_id}_{file.filename}")
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        report = Report(report_id=report_id, patient_name=patient_name,
                        token_number=token_number,
                        file_path=filename, remarks=remarks)
        report.set_password(password)
        db.session.add(report)
        db.session.commit()
        log_activity('Uploaded report', f'Patient: {patient_name}, RID: {report_id}')
        flash(f'Report uploaded! Report ID: {report_id} | Password: {password}', 'success')
        return redirect(url_for('admin.reports'))

    return render_template('admin/upload_report.html')


@admin.route('/reports')
@role_required('admin')
def reports():
    all_reports = Report.query.order_by(Report.uploaded_at.desc()).all()
    return render_template('admin/reports.html', reports=all_reports)


@admin.route('/reports/<int:report_id>/delete', methods=['POST'])
@role_required('admin')
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    # Delete file from disk
    upload_dir = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_dir, report.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    token = report.token_number
    db.session.delete(report)
    db.session.commit()
    log_activity('Deleted report', f'Token: {token}')
    flash(f'Report (Token: {token}) deleted. 🗑️', 'success')
    return redirect(url_for('admin.reports'))



# ── API: Test parameters for AJAX auto-fill ──
@admin.route('/api/test-parameters/<int:test_id>')
@role_required('admin')
def api_test_parameters(test_id):
    test = Test.query.get_or_404(test_id)
    params = TestParameter.query.filter_by(test_id=test_id)\
        .order_by(TestParameter.display_order).all()
    return jsonify({
        'test_name': test.name,
        'sample_type': test.sample_type,
        'parameters': [p.to_dict() for p in params]
    })


@admin.route('/create-report', methods=['GET', 'POST'])
@role_required('admin')
def create_report():
    all_tests = Test.query.filter_by(is_active=True)\
        .order_by(Test.name).all()
    categories = TestCategory.query.order_by(TestCategory.name).all()

    if request.method == 'POST':
        try:
            patient_name = request.form.get('patient_name', '').strip()
            age = request.form.get('age', '').strip()
            gender = request.form.get('gender', '').strip()
            doctor_name = request.form.get('doctor_name', '').strip()
            phone = request.form.get('phone', '').strip()
            test_id = request.form.get('test_id', '').strip()
            test_name = request.form.get('test_name', '').strip()
            sample_id = request.form.get('sample_id', '').strip()
            remarks = request.form.get('remarks', '').strip()
            sample_type = request.form.get('sample_type', 'Blood').strip()
            collection_date = request.form.get('collection_date', '').strip()
            report_time = request.form.get('report_time', '').strip()
            collected_at = request.form.get('collected_at', '').strip()

            if not patient_name or not test_name:
                flash('Patient Name and Test are required.', 'error')
                return render_template('admin/create_report.html',
                                       tests=all_tests, categories=categories)

            # Auto-generate sample_id if empty
            if not sample_id:
                sample_id = Report.generate_report_id()

            # Collect test parameters
            param_names = request.form.getlist('param_name[]')
            param_values = request.form.getlist('param_value[]')
            param_units = request.form.getlist('param_unit[]')
            param_ranges = request.form.getlist('param_range[]')

            test_results = []
            for i in range(len(param_names)):
                if param_names[i].strip():
                    test_results.append({
                        'parameter': param_names[i].strip(),
                        'value': param_values[i].strip() if i < len(param_values) else '',
                        'unit': param_units[i].strip() if i < len(param_units) else '',
                        'normal_range': param_ranges[i].strip() if i < len(param_ranges) else ''
                    })

            # Generate Report ID and password
            report_id = Report.generate_report_id()
            password = Report.generate_password_from_name(patient_name)

            # Report data dict
            report_data = {
                'report_id': report_id,
                'patient_name': patient_name,
                'age': age or 'N/A',
                'gender': gender or 'N/A',
                'doctor_name': doctor_name or 'Self',
                'phone': phone,
                'test_name': test_name,
                'token_number': sample_id,
                'sample_type': sample_type,
                'collection_date': collection_date,
                'report_time': report_time,
                'collected_at': collected_at,
                'remarks': remarks,
                'test_results': test_results
            }

            filename = secure_filename(f"{report_id}_{sample_id}.pdf")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            output_path = os.path.join(upload_dir, filename)

            # Download URL for QR code
            download_url = url_for('main.download_report_by_rid',
                                   report_id=report_id, _external=True)

            # Generate PDF
            generate_report_pdf(report_data, output_path, download_url)

            # Safe age conversion
            safe_age = None
            if age:
                try:
                    safe_age = int(age)
                except ValueError:
                    safe_age = None

            # Save to database
            report = Report(
                report_id=report_id,
                patient_name=patient_name,
                token_number=sample_id,
                file_path=filename,
                remarks=remarks,
                age=safe_age,
                gender=gender,
                doctor_name=doctor_name,
                test_name=test_name
            )
            report.set_password(password)
            report.set_test_results(test_results)
            db.session.add(report)
            db.session.commit()

            log_activity('Created report',
                         f'Patient: {patient_name}, RID: {report_id}')
            flash(f'Report created! ID: {report_id} | Password: {password}',
                  'success')
            return redirect(url_for('admin.report_preview',
                                    report_id=report_id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Report Creation Failed: {str(e)}")
            flash(f'Total failure during report creation: {str(e)}. (Check if Vercel storage is blocked)', 'error')
            return render_template('admin/create_report.html',
                                   tests=all_tests, categories=categories)

    return render_template('admin/create_report.html',
                           tests=all_tests, categories=categories)


@admin.route('/report/<report_id>/preview')
@role_required('admin')
def report_preview(report_id):
    report = Report.query.filter_by(report_id=report_id.upper()).first_or_404()
    test_results = report.get_test_results() if report.test_results_json else []
    templates = ReportTemplate.query.order_by(ReportTemplate.name).all()
    return render_template('admin/report_preview.html',
                           report=report, test_results=test_results,
                           templates=templates)


# ── Test Parameter Management ──
@admin.route('/tests/<int:test_id>/parameters')
@role_required('admin')
def test_parameters(test_id):
    test = Test.query.get_or_404(test_id)
    params = TestParameter.query.filter_by(test_id=test_id)\
        .order_by(TestParameter.display_order).all()
    return render_template('admin/test_parameters.html',
                           test=test, params=params)


@admin.route('/tests/<int:test_id>/parameters/add', methods=['POST'])
@role_required('admin')
def add_test_parameter(test_id):
    test = Test.query.get_or_404(test_id)
    name = request.form.get('parameter_name', '').strip()
    if not name:
        flash('Parameter name is required.', 'error')
        return redirect(url_for('admin.test_parameters', test_id=test_id))

    max_order = db.session.query(func.max(TestParameter.display_order))\
        .filter_by(test_id=test_id).scalar() or 0

    param = TestParameter(
        test_id=test_id,
        parameter_name=name,
        unit=request.form.get('unit', '').strip(),
        normal_range_text=request.form.get('normal_range_text', '').strip(),
        normal_range_min=float(request.form.get('normal_range_min'))
            if request.form.get('normal_range_min') else None,
        normal_range_max=float(request.form.get('normal_range_max'))
            if request.form.get('normal_range_max') else None,
        display_order=max_order + 1
    )
    db.session.add(param)
    db.session.commit()
    log_activity('Added test parameter',
                 f'{name} to {test.name}')
    flash(f'Parameter "{name}" added.', 'success')
    return redirect(url_for('admin.test_parameters', test_id=test_id))


@admin.route('/test-parameter/<int:param_id>/delete', methods=['POST'])
@role_required('admin')
def delete_test_parameter(param_id):
    param = TestParameter.query.get_or_404(param_id)
    test_id = param.test_id
    name = param.parameter_name
    db.session.delete(param)
    db.session.commit()
    log_activity('Deleted test parameter', f'{name}')
    flash(f'Parameter "{name}" deleted.', 'success')
    return redirect(url_for('admin.test_parameters', test_id=test_id))


# ═══════════════════════════════════════════════════════
#  PATIENT / USER MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/patients')
@role_required('admin')
def patients():
    search = request.args.get('q', '').strip()
    query = User.query.filter_by(role='patient')
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%')
            )
        )
    all_patients = query.order_by(User.created_at.desc()).all()
    return render_template('admin/patients.html', patients=all_patients, search=search)


@admin.route('/users')
@role_required('admin')
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@role_required('admin')
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate yourself.', 'error')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'blocked'
    log_activity(f'User {status}', f'User: {user.name} ({user.email})')
    flash(f'User "{user.name}" has been {status}. ✅', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@role_required('admin')
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin.users'))
    user.role = 'admin' if user.role == 'patient' else 'patient'
    db.session.commit()
    log_activity(f'Changed user role', f'User: {user.name} → {user.role}')
    flash(f'User "{user.name}" role changed to {user.role}. ✅', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'error')
        return redirect(url_for('admin.users'))
    name = user.name
    db.session.delete(user)
    db.session.commit()
    log_activity('Deleted user', f'User: {name}')
    flash(f'User "{name}" deleted. 🗑️', 'success')
    return redirect(url_for('admin.users'))


# ═══════════════════════════════════════════════════════
#  TESTIMONIAL MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/testimonials')
@role_required('admin')
def testimonials():
    all_testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=all_testimonials)


@admin.route('/testimonials/add', methods=['GET', 'POST'])
@role_required('admin')
def add_testimonial():
    if request.method == 'POST':
        reviewer_name = request.form.get('reviewer_name', '').strip()
        rating = int(request.form.get('rating', 5))
        review = request.form.get('review', '').strip()
        is_approved = request.form.get('is_approved') == 'on'

        if not all([reviewer_name, review]):
            flash('Name and review are required.', 'error')
            return render_template('admin/testimonial_form.html', testimonial=None)

        t = Testimonial(reviewer_name=reviewer_name, rating=rating,
                        review=review, is_approved=is_approved)
        db.session.add(t)
        db.session.commit()
        log_activity('Added testimonial', f'From: {reviewer_name}')
        flash('Testimonial added! ✅', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonial_form.html', testimonial=None)


@admin.route('/testimonials/edit/<int:t_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_testimonial(t_id):
    t = Testimonial.query.get_or_404(t_id)

    if request.method == 'POST':
        t.reviewer_name = request.form.get('reviewer_name', '').strip()
        t.rating = int(request.form.get('rating', 5))
        t.review = request.form.get('review', '').strip()
        t.is_approved = request.form.get('is_approved') == 'on'
        db.session.commit()
        log_activity('Updated testimonial', f'From: {t.reviewer_name}')
        flash('Testimonial updated! ✅', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonial_form.html', testimonial=t)


@admin.route('/testimonials/<int:t_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_testimonial(t_id):
    t = Testimonial.query.get_or_404(t_id)
    t.is_approved = not t.is_approved
    db.session.commit()
    status = 'approved' if t.is_approved else 'hidden'
    flash(f'Testimonial {status}. ✅', 'success')
    return redirect(url_for('admin.testimonials'))


@admin.route('/testimonials/<int:t_id>/delete', methods=['POST'])
@role_required('admin')
def delete_testimonial(t_id):
    t = Testimonial.query.get_or_404(t_id)
    db.session.delete(t)
    db.session.commit()
    log_activity('Deleted testimonial', f'ID: {t_id}')
    flash('Testimonial deleted. 🗑️', 'success')
    return redirect(url_for('admin.testimonials'))


# ═══════════════════════════════════════════════════════
#  DOCTOR REFERRALS
# ═══════════════════════════════════════════════════════
@admin.route('/referrals')
@role_required('admin')
def referrals():
    all_referrals = DoctorReferral.query.order_by(DoctorReferral.created_at.desc()).all()
    return render_template('admin/referrals.html', referrals=all_referrals)


@admin.route('/referrals/add', methods=['GET', 'POST'])
@role_required('admin')
def add_referral():
    if request.method == 'POST':
        doctor_name = request.form.get('doctor_name', '').strip()
        doctor_phone = request.form.get('doctor_phone', '').strip()
        patient_name = request.form.get('patient_name', '').strip()
        test_name = request.form.get('test_name', '').strip()
        notes = request.form.get('notes', '').strip()

        if not doctor_name:
            flash('Doctor name is required.', 'error')
            return render_template('admin/referral_form.html', referral=None)

        ref = DoctorReferral(doctor_name=doctor_name, doctor_phone=doctor_phone,
                             patient_name=patient_name, test_name=test_name, notes=notes)
        db.session.add(ref)
        db.session.commit()
        log_activity('Added referral', f'Doctor: {doctor_name}')
        flash('Referral added! ✅', 'success')
        return redirect(url_for('admin.referrals'))

    return render_template('admin/referral_form.html', referral=None)


@admin.route('/referrals/<int:ref_id>/delete', methods=['POST'])
@role_required('admin')
def delete_referral(ref_id):
    ref = DoctorReferral.query.get_or_404(ref_id)
    db.session.delete(ref)
    db.session.commit()
    log_activity('Deleted referral', f'ID: {ref_id}')
    flash('Referral deleted. 🗑️', 'success')
    return redirect(url_for('admin.referrals'))


# ═══════════════════════════════════════════════════════
#  CONTACT ENQUIRIES
# ═══════════════════════════════════════════════════════
@admin.route('/enquiries')
@role_required('admin')
def enquiries():
    all_enquiries = ContactEnquiry.query.order_by(ContactEnquiry.created_at.desc()).all()
    return render_template('admin/enquiries.html', enquiries=all_enquiries)


@admin.route('/enquiries/<int:enquiry_id>/read', methods=['POST'])
@role_required('admin')
def mark_read(enquiry_id):
    enquiry = ContactEnquiry.query.get_or_404(enquiry_id)
    enquiry.is_read = True
    db.session.commit()
    return redirect(url_for('admin.enquiries'))


@admin.route('/enquiries/<int:enquiry_id>/delete', methods=['POST'])
@role_required('admin')
def delete_enquiry(enquiry_id):
    enquiry = ContactEnquiry.query.get_or_404(enquiry_id)
    db.session.delete(enquiry)
    db.session.commit()
    log_activity('Deleted enquiry', f'From: {enquiry.name}')
    flash('Enquiry deleted. 🗑️', 'success')
    return redirect(url_for('admin.enquiries'))


# ═══════════════════════════════════════════════════════
#  REVENUE & ANALYTICS
# ═══════════════════════════════════════════════════════
@admin.route('/analytics')
@role_required('admin')
def analytics():
    today = datetime.utcnow().date()

    # Today's stats
    today_bookings = Booking.query.filter(
        func.date(Booking.booking_date) == today
    ).count()
    today_revenue = db.session.query(func.sum(Test.price)).join(
        Booking, Booking.test_id == Test.id
    ).filter(Booking.status == 'completed',
             func.date(Booking.booking_date) == today).scalar() or 0

    # This month
    month_start = today.replace(day=1)
    monthly_bookings = Booking.query.filter(Booking.booking_date >= month_start).count()
    monthly_revenue = db.session.query(func.sum(Test.price)).join(
        Booking, Booking.test_id == Test.id
    ).filter(Booking.status == 'completed',
             Booking.booking_date >= month_start).scalar() or 0

    # Total all time
    total_revenue = db.session.query(func.sum(Test.price)).join(
        Booking, Booking.test_id == Test.id
    ).filter(Booking.status == 'completed').scalar() or 0

    # Top tests (most booked)
    top_tests = db.session.query(
        Test.name, func.count(Booking.id).label('count')
    ).join(Booking, Booking.test_id == Test.id
    ).group_by(Test.name).order_by(func.count(Booking.id).desc()).limit(5).all()

    # Booking status breakdown
    status_counts = db.session.query(
        Booking.status, func.count(Booking.id)
    ).group_by(Booking.status).all()

    # Recent activity
    recent_activity = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return render_template('admin/analytics.html',
                           today_bookings=today_bookings,
                           today_revenue=today_revenue,
                           monthly_bookings=monthly_bookings,
                           monthly_revenue=monthly_revenue,
                           total_revenue=total_revenue,
                           top_tests=top_tests,
                           status_counts=dict(status_counts),
                           recent_activity=recent_activity)


# ═══════════════════════════════════════════════════════
#  ACTIVITY LOGS
# ═══════════════════════════════════════════════════════
@admin.route('/activity-log')
@role_required('admin')
def activity_log():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return render_template('admin/activity_log.html', logs=logs)




@admin.route('/settings', methods=['GET', 'POST'])
@role_required('admin')
def settings():
    if request.method == 'POST':
        keys = ['lab_name', 'lab_phone', 'lab_email', 'lab_address',
                'lab_hours', 'lab_tagline', 'lab_whatsapp']
        for key in keys:
            value = request.form.get(key, '').strip()
            setting = SiteSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SiteSettings(key=key, value=value)
                db.session.add(setting)
        db.session.commit()
        log_activity('Updated site settings')
        flash('Settings saved! ✅', 'success')
        return redirect(url_for('admin.settings'))

    # Load current settings
    settings_dict = {}
    for s in SiteSettings.query.all():
        settings_dict[s.key] = s.value

    return render_template('admin/settings.html', settings=settings_dict)


# ═══════════════════════════════════════════════════════
#  CSV EXPORTS
# ═══════════════════════════════════════════════════════
@admin.route('/export/patients')
@role_required('admin')
def export_patients():
    patients = User.query.filter_by(role='patient').all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Address', 'Bookings', 'Joined'])
    for p in patients:
        writer.writerow([p.id, p.name, p.email, p.phone, p.address,
                         len(p.bookings), p.created_at.strftime('%Y-%m-%d')])
    log_activity('Exported patients CSV')
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=patients.csv'})


@admin.route('/export/bookings')
@role_required('admin')
def export_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Patient', 'Test', 'Date', 'Time', 'Status',
                     'Home Collection', 'Payment', 'Created'])
    for b in bookings:
        writer.writerow([b.id, b.user.name, b.test.name,
                         b.booking_date.strftime('%Y-%m-%d'), b.slot_time,
                         b.status, 'Yes' if b.home_collection else 'No',
                         b.payment_status, b.created_at.strftime('%Y-%m-%d')])
    log_activity('Exported bookings CSV')
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=bookings.csv'})


@admin.route('/export/reports')
@role_required('admin')
def export_reports():
    reports = Report.query.order_by(Report.uploaded_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Patient Name', 'Token Number', 'Remarks', 'Uploaded'])
    for r in reports:
        writer.writerow([r.id, r.patient_name, r.token_number,
                         r.remarks, r.uploaded_at.strftime('%Y-%m-%d')])
    log_activity('Exported reports CSV')
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=reports.csv'})


# ═══════════════════════════════════════════════════════
#  REPORT TEMPLATE MANAGEMENT
# ═══════════════════════════════════════════════════════
@admin.route('/report-templates')
@role_required('admin')
def report_templates():
    templates = ReportTemplate.query.order_by(ReportTemplate.created_at.desc()).all()
    return render_template('admin/report_templates.html', templates=templates)


@admin.route('/report-templates/upload', methods=['POST'])
@role_required('admin')
def upload_template():
    name = request.form.get('name', '').strip()
    file = request.files.get('template_file')
    if not name or not file:
        flash('Template name and file are required.', 'error')
        return redirect(url_for('admin.report_templates'))

    allowed = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        flash('Only image files (PNG, JPG, WEBP) are allowed.', 'error')
        return redirect(url_for('admin.report_templates'))

    tpl_dir = os.path.join(current_app.static_folder, 'images', 'templates')
    os.makedirs(tpl_dir, exist_ok=True)
    filename = secure_filename(f"tpl_{int(datetime.utcnow().timestamp())}_{file.filename}")
    file.save(os.path.join(tpl_dir, filename))

    tpl = ReportTemplate(name=name, file_path=filename)
    db.session.add(tpl)
    db.session.commit()
    log_activity('Uploaded report template', name)
    flash(f'Template "{name}" uploaded!', 'success')
    return redirect(url_for('admin.report_templates'))


@admin.route('/report-templates/<int:tpl_id>/delete', methods=['POST'])
@role_required('admin')
def delete_template(tpl_id):
    tpl = ReportTemplate.query.get_or_404(tpl_id)
    # Delete file
    tpl_path = os.path.join(current_app.static_folder, 'images', 'templates', tpl.file_path)
    if os.path.exists(tpl_path):
        os.remove(tpl_path)
    name = tpl.name
    db.session.delete(tpl)
    db.session.commit()
    log_activity('Deleted report template', name)
    flash(f'Template "{name}" deleted.', 'success')
    return redirect(url_for('admin.report_templates'))
