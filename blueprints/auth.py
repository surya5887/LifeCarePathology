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
        # Support both 'login_id' (legacy) and 'email' (current template)
        login_id = request.form.get('email', request.form.get('login_id', '')).strip()
        password = request.form.get('password', '')

        # Check for Email OR Phone
        user = User.query.filter((User.email == login_id) | (User.phone == login_id)).first()

        if user and user.password_hash and user.check_password(password):
            login_user(user)
            
            # Smart Redirect
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                 return redirect(next_page)

            if user.is_admin():
                flash(f'Welcome back, {user.name.split()[0]}! 🎉', 'success') # Simplified name display
                return redirect(url_for('admin.dashboard'))
            
            flash(f'Welcome back, {user.name}! 🎉', 'success')
            return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid email/phone or password. Please try again.', 'error')

    return render_template('auth/login.html')


# --- OTP Helper Functions (Inlined for Vercel Stability) ---
def generate_otp(length=6):
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email, otp, purpose="Registration"):
    try:
        from flask_mail import Message
        from extensions import mail
        
        subject_map = {
            "Registration": "Verify Account - LifeCare Pathology",
            "Login": "Login OTP - LifeCare Pathology",
            "Reset": "Reset Password - LifeCare Pathology"
        }
        subject = subject_map.get(purpose, "Verification Code")

        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=f"Your {purpose} verification code is: {otp}\n\nValid for 10 minutes.",
            html=f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; max-width: 500px;">
                <h2 style="color: #FFC107;">LifeCare Pathology Lab</h2>
                <p>Hello,</p>
                <p>Use the code below for <strong>{purpose}</strong>:</p>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; margin: 20px 0;">
                    {otp}
                </div>
                <p>If you did not request this, please ignore this email.</p>
            </div>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending OTP to {to_email}: {e}")
        return False
# -----------------------------------------------------------

@auth.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        purpose = data.get('purpose', 'Registration') # Registration, Login, Reset

        if not email:
            return jsonify({'success': False, 'message': 'Email is required.'}), 400

        user = User.query.filter_by(email=email).first()

        # Contextual Validation
        if purpose == 'Registration':
            if user:
                return jsonify({'success': False, 'message': 'Email already registered. Login instead.'}), 400
        elif purpose in ['Login', 'Reset']:
            if not user:
                return jsonify({'success': False, 'message': 'Email not found. Please register first.'}), 404

        # Generate OTP
        otp = generate_otp()
        
        # Store in Session
        session['otp'] = otp
        session['otp_email'] = email
        session['otp_purpose'] = purpose
        session['email_verified'] = False

        # Send Email
        if send_otp_email(email, otp, purpose):
            return jsonify({'success': True, 'message': 'OTP sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP.'}), 500

    except Exception as e:
        print(f"OTP Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500


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

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
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


    # Remove debug route



# ============================================================
#                    OAUTH SOCIAL LOGIN
# ============================================================
from authlib.integrations.flask_client import OAuth

oauth = OAuth()
_registered_providers = set()  # Track which providers are actually configured


# --- DATABASE MIGRATION HELPER (Run once) ---
@auth.route('/db-migrate-oauth')
def db_migrate_oauth():
    from sqlalchemy import text
    results = []
    try:
        # 1. Add oauth_provider
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20)"))
            db.session.commit()
            results.append("Added oauth_provider column")
        except Exception as e:
            db.session.rollback()
            results.append(f"oauth_provider column likely exists ({str(e)})")

        # 2. Add oauth_id
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(200)"))
            db.session.commit()
            results.append("Added oauth_id column")
        except Exception as e:
            db.session.rollback()
            results.append(f"oauth_id column likely exists ({str(e)})")

        # 3. Make phone nullable
        try:
            db.session.execute(text("ALTER TABLE users ALTER COLUMN phone DROP NOT NULL"))
            db.session.commit()
            results.append("Made phone nullable")
        except Exception as e:
            db.session.rollback()
            results.append(f"Phone alter failed: {str(e)}")

        # 4. Make password_hash nullable
        try:
            db.session.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            db.session.commit()
            results.append("Made password_hash nullable")
        except Exception as e:
            db.session.rollback()
            results.append(f"Password alter failed: {str(e)}")
            
        # 5. Add profile_pic
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(300)"))
            db.session.commit()
            results.append("Added profile_pic column")
        except Exception as e:
            db.session.rollback()
            results.append(f"profile_pic column likely exists ({str(e)})")
            
        return jsonify(results)
    except Exception as e:
        return f"Migration Error: {str(e)}"

def init_oauth(app):
    """Initialize OAuth with the Flask app."""
    oauth.init_app(app)

    # Google
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
        _registered_providers.add('google')
        print(f"✅ Google OAuth registered with client_id: {app.config['GOOGLE_CLIENT_ID'][:20]}...")
    else:
        print("⚠️ Google OAuth not configured (GOOGLE_CLIENT_ID missing)")




def _handle_oauth_user(provider, oauth_id, email, name, picture=None):
    """Find or create user from OAuth data, then log them in."""
    # 1. Check by oauth_id
    user = User.query.filter_by(oauth_provider=provider, oauth_id=str(oauth_id)).first()

    if not user:
        # 2. Check by email — link existing account
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account
            user.oauth_provider = provider
            user.oauth_id = str(oauth_id)
            if picture and not user.profile_pic:
                user.profile_pic = picture
            db.session.commit()
        else:
            # 3. Create new user
            user = User(
                name=name or email.split('@')[0],
                email=email,
                phone='',
                oauth_provider=provider,
                oauth_id=str(oauth_id),
                profile_pic=picture,
                role='patient'
            )
            db.session.add(user)
            db.session.commit()
    else:
        # Update profile pic if new one available and different
        if picture and user.profile_pic != picture:
            user.profile_pic = picture
            db.session.commit()

    login_user(user)
    flash(f'Welcome, {user.name}! 🎉', 'success')

    if user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('patient.dashboard'))


# --- Google OAuth Routes ---
@auth.route('/auth/google')
def google_login():
    if 'google' not in _registered_providers:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.google_callback', _external=True)
    if redirect_uri.startswith('http://'):
        redirect_uri = redirect_uri.replace('http://', 'https://', 1)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route('/auth/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.google.userinfo()

        email = user_info.get('email')
        name = user_info.get('name', '')
        oauth_id = user_info.get('sub')
        picture = user_info.get('picture', '')

        if not email:
            flash('Could not retrieve email from Google.', 'error')
            return redirect(url_for('auth.login'))

        _handle_oauth_user('google', oauth_id, email, name, picture)
        return redirect(url_for('patient.dashboard'))

    except Exception as e:
        print(f"Google OAuth Error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Google login failed: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


# ============================================================
#                    PASSWORD RESET & OTP LOGIN
# ============================================================

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    return render_template('auth/forgot_password.html')

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('password', '')

        # Session Checks
        if not session.get('otp') or session.get('otp_email') != email or session.get('otp_purpose') != 'Reset':
             flash('Invalid or expired OTP session. Please try again.', 'error')
             return redirect(url_for('auth.forgot_password'))

        if otp != session['otp']:
             flash('Invalid OTP.', 'error')
             return render_template('auth/reset_password.html', email=email)

        # Update Password
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            
            # Clear session
            session.pop('otp', None)
            session.pop('otp_email', None)
            session.pop('otp_purpose', None)

            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
             flash('User not found.', 'error')

    email = request.args.get('email', '')
    return render_template('auth/reset_password.html', email=email)


@auth.route('/otp-login', methods=['GET', 'POST'])
def otp_login():
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    return render_template('auth/otp_login.html')

@auth.route('/verify-otp-login', methods=['POST'])
def verify_otp_login():
    email = request.form.get('email', '').strip()
    otp = request.form.get('otp', '').strip()

    if not session.get('otp') or session.get('otp_email') != email or session.get('otp_purpose') != 'Login':
            flash('Invalid or expired OTP session.', 'error')
            return redirect(url_for('auth.otp_login'))
    
    if otp == session['otp']:
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            # Clear session
            session.pop('otp', None)
            session.pop('otp_email', None)
            session.pop('otp_purpose', None)
            
            flash(f'Welcome back, {user.name}! 🎉', 'success')
            return redirect(url_for('patient.dashboard'))
    
    flash('Invalid OTP.', 'error')
    return redirect(url_for('auth.otp_login', email=email))

