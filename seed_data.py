from models import User, TestCategory
from extensions import db


def seed_database():

    # Prevent duplicate seeding
    if User.query.filter_by(email="admin@lifecare.com").first():
        return

    print("Seeding database...")

    # Create Admin
    admin = User(
        name="Admin",
        email="admin@lifecare.com",
        phone="9999999999",
        role="admin"
    )
    admin.set_password("admin123")
    db.session.add(admin)

    # Categories
    categories = [
        "Hematology",
        "Biochemistry",
        "Microbiology",
        "Serology",
        "Urinalysis",
        "Thyroid",
        "Diabetes"
    ]

    for name in categories:
        db.session.add(TestCategory(name=name, icon="fa-flask"))

    db.session.commit()

    print("Database seeded successfully.")
