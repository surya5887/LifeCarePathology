from app import create_app
from extensions import db
from models import User, TestCategory, Test, Testimonial
from werkzeug.security import generate_password_hash

app = create_app()

def seed_data():
    with app.app_context():
        # 1. Create Admin User
        admin_email = 'admin@lifecare.com'
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                name='Dr. Admin',
                email=admin_email,
                phone='9876543210',
                role='admin',
                address='Life Care Lab, Asara',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            print("Admin user created (admin@lifecare.com / admin123)")

        # 2. Create Test Categories
        categories = [
            ('Hematology', '🩸', 'Blood related tests'),
            ('Biochemistry', '🧪', 'Liver, Kidney, Lipid profiles'),
            ('Microbiology', '🧫', 'Infection and culture tests'),
            ('Thyroid', '🦋', 'T3, T4, TSH monitoring'),
            ('Diabetes', '🍬', 'Blood sugar and HbA1c'),
            ('Urine Analysis', '🚽', 'Routine urine examination'),
            ('Serology', '💉', 'Infectious diseases'),
            ('Radiology', '🦴', 'X-Ray and scans')
        ]

        cat_objs = {}
        for name, icon, desc in categories:
            cat = TestCategory.query.filter_by(name=name).first()
            if not cat:
                cat = TestCategory(name=name, icon=icon, description=desc)
                db.session.add(cat)
                print(f"Category '{name}' added")

        db.session.commit()

        # 3. Create Tests
        # Refresh category objects
        cat_objs = {}
        for name, _, _ in categories:
            cat_objs[name] = TestCategory.query.filter_by(name=name).first()

        tests_data = [
            # Hematology
            ('Complete Blood Count (CBC)', 'Hematology', 350, 'Includes Hemoglobin, RBC, WBC, Platelets', 'Blood'),
            ('Blood Group & Rh', 'Hematology', 150, 'Determination of blood group', 'Blood'),
            ('ESR', 'Hematology', 100, 'Erythrocyte Sedimentation Rate', 'Blood'),
            
            # Biochemistry
            ('Liver Function Test (LFT)', 'Biochemistry', 800, 'Bilirubin, SGOT, SGPT, ALP, Proteins', 'Blood'),
            ('Kidney Function Test (KFT)', 'Biochemistry', 900, 'Urea, Creatinine, Uric Acid', 'Blood'),
            ('Lipid Profile', 'Biochemistry', 750, 'Cholesterol, Triglycerides, HDL, LDL', 'Blood'),
            
            # Thyroid
            ('Thyroid Profile (T3, T4, TSH)', 'Thyroid', 600, 'Complete thyroid function assessment', 'Blood'),
            ('TSH Ultra Sensitive', 'Thyroid', 350, 'Thyroid Stimulating Hormone', 'Blood'),

            # Diabetes
            ('Blood Sugar (Fasting)', 'Diabetes', 80, 'Fasting plasma glucose', 'Blood'),
            ('Blood Sugar (PP)', 'Diabetes', 80, 'Post-prandial glucose', 'Blood'),
            ('HbA1c', 'Diabetes', 500, 'Average blood sugar of last 3 months', 'Blood'),

            # Urine
            ('Urine Routine & Microscopy', 'Urine Analysis', 150, 'Physical, Chemical and Microscopic exam', 'Urine'),
            ('Urine Culture', 'Urine Analysis', 600, 'Bacterial culture and sensitivity', 'Urine'),

            # Serology
            ('Dengue NS1 Antigen', 'Serology', 900, 'Early detection of Dengue', 'Blood'),
            ('Typhoid (Widal)', 'Serology', 200, 'Test for Enteric Fever', 'Blood'),
            ('Hepatitis B (HBsAg)', 'Serology', 400, 'Screening for Hepatitis B', 'Blood'),
        ]

        for t_name, cat_name, price, desc, sample in tests_data:
            if not Test.query.filter_by(name=t_name).first():
                test = Test(
                    name=t_name,
                    category_id=cat_objs[cat_name].id,
                    price=price,
                    description=desc,
                    sample_type=sample,
                    report_time='24 Hours'
                )
                db.session.add(test)
                print(f"Test '{t_name}' added")

        # 4. Create Sample Testimonials
        if Testimonial.query.count() == 0:
            t1 = Testimonial(reviewer_name='Rahul Sharma', rating=5, review='Excellent service! The home collection was on time and reports were delivered very fast.', is_approved=True)
            t2 = Testimonial(reviewer_name='Priya Verma', rating=5, review='Very hygienic lab and polite staff. Highly recommended for family health checkups.', is_approved=True)
            t3 = Testimonial(reviewer_name='Amit Kumar', rating=4, review='Good experience. The online report download feature is very convenient.', is_approved=True)
            db.session.add_all([t1, t2, t3])
            print("Sample testimonials added")

        db.session.commit()
        print("\nDatabase seeding completed successfully!")

if __name__ == '__main__':
    seed_data()
