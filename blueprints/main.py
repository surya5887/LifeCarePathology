from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from models import Test, TestCategory, ContactEnquiry, Testimonial, Report
from extensions import db
import os

main = Blueprint('main', __name__)


@main.route('/')
def home():
    categories = TestCategory.query.all()
    popular_tests = Test.query.filter_by(is_active=True).limit(6).all()
    testimonials = Testimonial.query.filter_by(is_approved=True).order_by(Testimonial.created_at.desc()).limit(6).all()
    return render_template('home.html', categories=categories, popular_tests=popular_tests, testimonials=testimonials)


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/services')
def services():
    categories = TestCategory.query.all()
    selected_category = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()

    query = Test.query.filter_by(is_active=True)

    if selected_category:
        query = query.filter_by(category_id=int(selected_category))

    if search_query:
        query = query.filter(Test.name.ilike(f'%{search_query}%'))

    tests = query.order_by(Test.name).all()
    return render_template('services.html', tests=tests, categories=categories,
                           selected_category=selected_category, search_query=search_query)


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not message:
            flash('Please provide your name and message.', 'error')
            return render_template('contact.html')

        enquiry = ContactEnquiry(name=name, email=email, phone=phone, message=message)
        db.session.add(enquiry)
        db.session.commit()

        flash('Thank you! Your message has been sent successfully. We will get back to you soon. ✅', 'success')
        return redirect(url_for('main.contact'))

    return render_template('contact.html')


@main.route('/check-report', methods=['GET', 'POST'])
def check_report():
    report = None
    error = None

    if request.method == 'POST':
        token = request.form.get('token_number', '').strip()
        password = request.form.get('password', '').strip()

        if not token or not password:
            error = 'Please enter both Token Number and Password.'
        else:
            report_obj = Report.query.filter_by(token_number=token).first()
            if report_obj and report_obj.check_password(password):
                report = report_obj
            else:
                error = 'Invalid Token Number or Password. Please check and try again.'

    return render_template('check_report.html', report=report, error=error)


@main.route('/download-report/<int:report_id>')
def download_report(report_id):
    report = Report.query.get_or_404(report_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], report.file_path)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True,
                         download_name=f'Report_{report.token_number}.pdf')
    flash('Report file not found. Please contact the lab.', 'error')
    return redirect(url_for('main.check_report'))
