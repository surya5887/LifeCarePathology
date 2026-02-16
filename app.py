import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate
from models import User
from error_handlers import register_error_handlers
from seed_data import seed_database


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

    # Create DB + upload folder + seed
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        seed_database()

    return app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
