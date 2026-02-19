import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate, mail
from models import User
from models import User
try:
    from error_handlers import register_error_handlers
except ImportError:
    def register_error_handlers(app): pass



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    try:
        mail.init_app(app)
    except Exception as e:
        print(f"Warning: Mail init failed: {e}")

    # Login configuration
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Register blueprints
    from blueprints.auth import auth
    from blueprints.main import main
    from blueprints.patient import patient
    from blueprints.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(patient)
    app.register_blueprint(admin)


    @app.route('/test-email')
    def test_email():
        try:
            from flask_mail import Message
            from extensions import mail
            
            msg = Message(
                "Test Email from LifeCare",
                recipients=['anishchaudhary0078@gmail.com'],  # Sending to self to test
                body="If you receive this, email configuration is working!"
            )
            mail.send(msg)
            return "<h1>Email Sent Successfully! ✅</h1><p>Check your inbox.</p>"
        except Exception as e:
            import traceback
            return f"<h1>Email Failed ❌</h1><pre>{str(e)}</pre><pre>{traceback.format_exc()}</pre>"


    @app.route('/debug-otp-flow')
    def debug_otp_flow():
        logs = []
        try:
            logs.append("1. Starting Debug Flow...")
            
            # 1. Test Import
            logs.append("2. Importing modules...")
            from flask import session
            import random, string
            from extensions import db, mail
            from models import User
            from flask_mail import Message
            logs.append("   - Imports successful.")

            # 2. Test DB Connection
            logs.append("3. Testing DB Connection (User Query)...")
            try:
                user_count = User.query.count()
                logs.append(f"   - DB Connected. User Count: {user_count}")
            except Exception as e:
                logs.append(f"   - DB Connection Failed: {e}")
                raise e

            # 3. Test Session Write
            logs.append("4. Testing Session Write...")
            try:
                session['debug_check'] = 'working'
                logs.append("   - Session written.")
            except Exception as e:
                 logs.append(f"   - Session Write Failed: {e}")
                 # We don't raise here, as email might still work

            # 4. Test Email Sending
            logs.append("5. Sending Email...")
            try:
                msg = Message(
                    "Debug OTP Flow",
                    recipients=['anishchaudhary0078@gmail.com'],
                    body="Debug flow working."
                )
                mail.send(msg)
                logs.append("   - Email sent.")
            except Exception as e:
                logs.append(f"   - Email Failed: {e}")
                raise e

            return f"<h1>Debug Success ✅</h1><pre>" + "\n".join(logs) + "</pre>"

        except Exception as e:
            import traceback
            return f"<h1>Debug Failed ❌</h1><pre>" + "\n".join(logs) + f"\n\nERROR: {str(e)}\n\n{traceback.format_exc()}</pre>"


    # Create DB + upload folder + auto-seed admin
    with app.app_context():
        try:
            db.create_all()
            try:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            except OSError:
                print("WARNING: Could not create upload folder (Read-only filesystem?)")

            # Auto-create admin if none exists
            if not User.query.filter_by(role='admin').first():
                admin_user = User(
                    name='Admin',
                    email='admin@lifecare.com',
                    phone='9999999999',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print('✅ Default admin user created: admin@lifecare.com / admin123')
        except Exception as e:
            print(f"⚠️ Startup Database Connection Failed: {e}")
            # We do NOT raise the error, so the app can still start and show debug pages


    return app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
