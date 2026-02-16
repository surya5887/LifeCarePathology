import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Test, TestCategory, Booking, Report, ContactEnquiry, Testimonial
from models import Report
from extensions import db
from functools import wraps
from utils import role_required
from file_utils import validate_pdf

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function


@admin.before_request
@login_required
def before_request():
    pass


# ─── Dashboard ─────────────────────────────────────────
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

    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           total_tests=total_tests,
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           total_reports=total_reports,
                           unread_enquiries=unread_enquiries,
                           recent_bookings=recent_bookings)


# ─── Test Management ───────────────────────────────────
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

        test = Test(
            name=name,
            category_id=int(category_id),
            price=float(price),
            description=description,
            sample_type=sample_type,
            report_time=report_time
        )
        db.session.add(test)
        db.session.commit()
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
    flash(f'Test "{name}" deleted. 🗑️', 'success')
    return redirect(url_for('admin.tests'))


# ─── Appointments / Bookings ──────────────────────────
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
        flash(f'Booking #{booking.id} status updated to {new_status}. ✅', 'success')
    return redirect(url_for('admin.appointments'))


# ─── Report Upload ─────────────────────────────────────
@admin.route('/upload-report', methods=['GET', 'POST'])
@role_required('admin')
def upload_report():

    if request.method == 'POST':

        patient_name = request.form.get('patient_name')
        token_number = request.form.get('token_number')
        password = request.form.get('password')
        remarks = request.form.get('remarks')
        file = request.files.get('report_file')

        # Basic field validation
        if not all([patient_name, token_number, password, file]):
            flash('Please fill all fields and select a PDF file.', 'error')
            return render_template('admin/upload_report.html')

        # Duplicate token check
        if Report.query.filter_by(token_number=token_number).first():
            flash('Token number already exists. Please use a unique token.', 'error')
            return render_template('admin/upload_report.html')

        # Validate PDF file
        is_valid, error_msg = validate_pdf(file)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('admin/upload_report.html')

        # Save file
        filename = secure_filename(f"{token_number}_{file.filename}")
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Create report entry
        report = Report(
            patient_name=patient_name,
            token_number=token_number,
            file_path=filename,
            remarks=remarks
        )

        report.set_password(password)

        db.session.add(report)
        db.session.commit()

        flash('Report uploaded successfully!', 'success')
        return redirect(url_for('admin.reports'))

    return render_template('admin/upload_report.html')


@admin.route('/reports')
@role_required('admin')
def reports():
    all_reports = Report.query.order_by(Report.uploaded_at.desc()).all()
    return render_template('admin/reports.html', reports=all_reports)


# ─── Patient Management ───────────────────────────────
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


# ─── Contact Enquiries ────────────────────────────────
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
