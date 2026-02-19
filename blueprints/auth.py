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

        if user and user.password_hash and user.check_password(password):
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


# --- OTP Helper Functions (Inlined for Vercel Stability) ---
def generate_otp(length=6):
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email, otp):
    try:
        from flask_mail import Message
        from extensions import mail
        
        msg = Message(
            subject="Your Verification Code - LifeCare Pathology",
            recipients=[to_email],
            body=f"Your verification code is: {otp}\n\nThis code is valid for 10 minutes.",
            html=f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; max-width: 500px;">
                <h2 style="color: #FFC107;">LifeCare Pathology Lab</h2>
                <p>Hello,</p>
                <p>Please use the verification code below to complete your registration:</p>
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

        if not email:
            return jsonify({'success': False, 'message': 'Email is required.'}), 400

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email is already registered. Please login.'}), 400

        # Generate OTP
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

    # Microsoft / Outlook
    if app.config.get('MICROSOFT_CLIENT_ID'):
        oauth.register(
            name='microsoft',
            client_id=app.config['MICROSOFT_CLIENT_ID'],
            client_secret=app.config['MICROSOFT_CLIENT_SECRET'],
            server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
        _registered_providers.add('microsoft')
        print("✅ Microsoft OAuth registered")

    # Facebook
    if app.config.get('FACEBOOK_CLIENT_ID'):
        oauth.register(
            name='facebook',
            client_id=app.config['FACEBOOK_CLIENT_ID'],
            client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
            access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
            authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
            api_base_url='https://graph.facebook.com/v18.0/',
            client_kwargs={'scope': 'email public_profile'},
        )
        _registered_providers.add('facebook')
        print("✅ Facebook OAuth registered")


def _handle_oauth_user(provider, oauth_id, email, name):
    """Find or create user from OAuth data, then log them in."""
    # 1. Check by oauth_id
    user = User.query.filter_by(oauth_provider=provider, oauth_id=str(oauth_id)).first()

    if not user:
        # 2. Check by email — link existing account
        user = User.query.filter_by(email=email).first()
        if user:
            user.oauth_provider = provider
            user.oauth_id = str(oauth_id)
            db.session.commit()
        else:
            # 3. Create new user
            user = User(
                name=name or email.split('@')[0],
                email=email,
                phone='',
                oauth_provider=provider,
                oauth_id=str(oauth_id),
                role='patient'
            )
            db.session.add(user)
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

        if not email:
            flash('Could not get email from Google.', 'error')
            return redirect(url_for('auth.login'))

        return _handle_oauth_user('google', oauth_id, email, name)

    except Exception as e:
        print(f"Google OAuth Error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Google login failed: {str(e)}', 'error')
        return redirect(url_for('auth.login'))


# --- Microsoft OAuth Routes ---
@auth.route('/auth/microsoft')
def microsoft_login():
    if 'microsoft' not in _registered_providers:
        flash('Microsoft login is not configured.', 'error')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    if redirect_uri.startswith('http://'):
        redirect_uri = redirect_uri.replace('http://', 'https://', 1)
    return oauth.microsoft.authorize_redirect(redirect_uri)


@auth.route('/auth/microsoft/callback')
def microsoft_callback():
    try:
        token = oauth.microsoft.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.microsoft.userinfo()

        email = user_info.get('email') or user_info.get('preferred_username')
        name = user_info.get('name', '')
        oauth_id = user_info.get('sub') or user_info.get('oid')

        if not email:
            flash('Could not get email from Microsoft.', 'error')
            return redirect(url_for('auth.login'))

        return _handle_oauth_user('microsoft', oauth_id, email, name)

    except Exception as e:
        print(f"Microsoft OAuth Error: {e}")
        import traceback
        traceback.print_exc()
        flash('Microsoft login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))


# --- Facebook OAuth Routes ---
@auth.route('/auth/facebook')
def facebook_login():
    if 'facebook' not in _registered_providers:
        flash('Facebook login is not configured.', 'error')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.facebook_callback', _external=True)
    if redirect_uri.startswith('http://'):
        redirect_uri = redirect_uri.replace('http://', 'https://', 1)
    return oauth.facebook.authorize_redirect(redirect_uri)


@auth.route('/auth/facebook/callback')
def facebook_callback():
    try:
        token = oauth.facebook.authorize_access_token()
        resp = oauth.facebook.get('me?fields=id,name,email')
        user_info = resp.json()

        email = user_info.get('email')
        name = user_info.get('name', '')
        oauth_id = user_info.get('id')

        if not email:
            flash('Could not get email from Facebook. Please ensure email permission is granted.', 'error')
            return redirect(url_for('auth.login'))

        return _handle_oauth_user('facebook', oauth_id, email, name)

    except Exception as e:
        print(f"Facebook OAuth Error: {e}")
        import traceback
        traceback.print_exc()
        flash('Facebook login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

