import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate
from models import User
from error_handlers import register_error_handlers



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Login configuration
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from blueprints.auth import auth
    from blueprints.main import main
    from blueprints.patient import patient
    from blueprints.admin import admin

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(patient)
    app.register_blueprint(admin)

    register_error_handlers(app)

    # Create DB + upload folder + auto-seed admin
    with app.app_context():
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


    return app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
