
from app import create_app
from extensions import db
from seed_parameters import seed_test_parameters
from seed_data import seed_data
import os

# Ensure we use the latest config with new password
app = create_app()

def init_database_local():
    # Override app config to use Pooler URL for local attempt
    # Pooler User: postgres.cvuvtnnpxjpjxndaqask
    # Password: Cyy%3FUg2DS_Zj%40%2Bq
    pooler_url = "postgresql://postgres.cvuvtnnpxjpjxndaqask:Cyy%3FUg2DS_Zj%40%2Bq@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    app.config['SQLALCHEMY_DATABASE_URI'] = pooler_url
    
    with app.app_context():
        print(f"Connecting to: {pooler_url.split('@')[1]}")
        
        print("Creating all tables...")
        try:
            db.create_all()
            print("✅ Tables created successfully.")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return

        print("Seeding initial data...")
        try:
            seed_test_parameters()
            seed_data()
            print("✅ Database seeding complete.")
        except Exception as e:
             print(f"❌ Error seeding data: {e}")

if __name__ == "__main__":
    init_database_local()
