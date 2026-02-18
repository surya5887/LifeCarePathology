
from app import create_app
from extensions import db
from seed_parameters import seed_test_parameters
from seed_data import seed_data
import models

app = create_app()

def init_database():
    with app.app_context():
        print("Creating all tables in new database...")
        db.create_all()
        print("✅ Tables created successfully.")

        print("Seeding initial data...")
        seed_test_parameters()
        seed_data()
        print("✅ Database seeding complete.")

if __name__ == "__main__":
    init_database()
