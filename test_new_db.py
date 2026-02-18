
import psycopg2
from urllib.parse import urlparse

# New Project Pooler URL (Transaction Mode)
# Format: postgresql://postgres.[project]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
DATABASE_URL = "postgresql://postgres.cvuvtnnpxjpjxndaqask:AmazingAnis7711%40@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def test_connection():
    try:
        print(f"Connecting to {DATABASE_URL.split('@')[1]}...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection Successful!")
        print(f"Database Version: {version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
