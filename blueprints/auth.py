import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import User
from extensions import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            
            # Smart Redirect
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                 return redirect(next_page)

            if user.is_admin():
                flash(f'Welcome back, Anees Chaudhary! 🎉', 'success')
                return redirect(url_for('admin.dashboard'))
            
            flash(f'Welcome back, {user.name}! 🎉', 'success')
            return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')

    return render_template('auth/login.html')


@auth.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'success': False, 'message': 'Email is required.'}), 400

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email is already registered. Please login.'}), 400

        # Generate OTP
        from utils.otp_util import generate_otp, send_otp_email
        otp = generate_otp()
        
        # Store in Session (Temporary)
        session['otp'] = otp
        session['otp_email'] = email
        session['email_verified'] = False

        # Send Email
        if send_otp_email(email, otp):
            return jsonify({'success': True, 'message': 'OTP sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP. Check email.'}), 500

    except Exception as e:
        print(f"OTP Error: {e}")
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500


@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        user_otp = data.get('otp', '').strip()

        if not email or not user_otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required.'}), 400

        # Verify against Session
        session_otp = session.get('otp')
        session_email = session.get('otp_email')

        if not session_otp or not session_email:
            return jsonify({'success': False, 'message': 'OTP expired. Please request a new one.'}), 400

        if email != session_email:
             return jsonify({'success': False, 'message': 'Email mismatch.'}), 400

        if user_otp == session_otp:
            session['email_verified'] = True
            return jsonify({'success': True, 'message': 'Email verified successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid OTP.'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, phone, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please login.', 'error')
            return render_template('auth/register.html')
            
        # OTP VERIFICATION CHECK
        if not session.get('email_verified') or session.get('otp_email') != email:
             flash('Please verify your email via OTP first.', 'error')
             return render_template('auth/register.html')

        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Clean session
        session.pop('otp', None)
        session.pop('otp_email', None)
        session.pop('email_verified', None)
        
        # Auto-Login
        login_user(user)

        flash('Registration successful! Welcome to LifeCare. ✅', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
