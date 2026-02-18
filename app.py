import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate, mail
from models import User
from error_handlers import register_error_handlers



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

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

    @app.route('/init-db')
    def init_db():
        try:
            # Force SSL mode for Supabase
            if 'sslmode' not in app.config['SQLALCHEMY_DATABASE_URI']:
                pass # SQLAlchemy usually handles this, but good to note
            
            db.create_all()
            return "Database Tables Created Successfully! ✅ <br> <a href='/seed-db'>Now Click Here to Seed Data</a>"
        except Exception as e:
            import traceback
            return f"<h1>Error creating tables</h1><pre>{str(e)}</pre><pre>{traceback.format_exc()}</pre>"

    @app.route('/debug-config')
    def debug_config():
        try:
            from sqlalchemy import text
            # Mask password in URL
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            safe_url = db_url.split('@')[-1] if '@' in db_url else "INVALID_URL"
            
            status = "Unknown"
            error = "None"
            
            try:
                db.session.execute(text("SELECT 1"))
                status = "Connected ✅"
            except Exception as e:
                status = "Connection Failed ❌"
                error = str(e)
            
            return f"""
            <h1>Debug Config</h1>
            <p><strong>Database Host:</strong> {safe_url}</p>
            <p><strong>Connection Status:</strong> {status}</p>
            <p><strong>Error Details:</strong> {error}</p>
            """
        except Exception as e:
            return f"Critical Debug Error: {e}"

    @app.route('/migrate-full')
    def migrate_full():
        try:
            import psycopg2
            from sqlalchemy import text
            
            # Source: Old DB (Direct Connection for Reliability)
            # Host: db.qtkrrwtorkmfhxakemjp.supabase.co
            # User: postgres (Standard)
            # Password: ANEES879176
            OLD_DB_URL = "postgresql://postgres:ANEES879176@db.qtkrrwtorkmfhxakemjp.supabase.co:5432/postgres"
            
            # Connect to Old DB
            conn_old = psycopg2.connect(OLD_DB_URL)
            cur_old = conn_old.cursor()
            
            # 1. Clear New DB (Target) - Order matters for FKs
            # We use CASCADE to handle dependencies
            db.session.execute(text("TRUNCATE TABLE users, test_parameters, bookings, contact_messages, reports CASCADE"))
            db.session.commit()
            
            tables = ['users', 'test_parameters', 'bookings', 'contact_messages', 'reports']
            log = []
            
            for table in tables:
                # Fetch from Old
                try:
                    cur_old.execute(f"SELECT * FROM {table}")
                    rows = cur_old.fetchall()
                    cols = [desc[0] for desc in cur_old.description]
                    
                    if not rows:
                        log.append(f"{table}: No data found.")
                        continue
                        
                    # Insert into New
                    # Construct INSERT statement dynamically
                    col_str = ', '.join(cols)
                    val_placeholders = ', '.join([':' + col for col in cols])
                    sql = text(f"INSERT INTO {table} ({col_str}) VALUES ({val_placeholders})")
                    
                    for row in rows:
                        row_dict = dict(zip(cols, row))
                        # Handle potential schema mismatch (remove extra cols if any, or handle missing)
                        # For now assume mostly identical
                        db.session.execute(sql, row_dict)
                    
                    log.append(f"{table}: Migrated {len(rows)} rows.")
                    
                except Exception as e:
                    log.append(f"{table} Error: {str(e)}")
                    # Continue to next table even if one fails
            
            db.session.commit()
            conn_old.close()
            
            return f"<h1>Migration Results</h1><pre>{'<br>'.join(log)}</pre>"
            
        except Exception as e:
            import traceback
            return f"<h1>Migration Failed</h1><pre>{str(e)}</pre><pre>{traceback.format_exc()}</pre>"

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
