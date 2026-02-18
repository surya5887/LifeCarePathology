import os
import psycopg2
from urllib.parse import urlparse

# URL from config.py
DATABASE_URL = "postgresql://postgres.qtkrrwtorkmfhxakemjp:AmazingAnis7711%40@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

def run_migration():
    try:
        # Parse URL
        result = urlparse(DATABASE_URL)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port

        print(f"Connecting to {hostname}:{port} as {username}...")
        
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Attempting to add profile_picture column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(255)")
        print("Successfully added profile_picture column (or it already existed).")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()
