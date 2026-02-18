
import psycopg2

# Old Project Info
# Project ID: qtkrrwtorkmfhxakemjp
# Pooler: aws-1-ap-southeast-1.pooler.supabase.com
# Password: ANEES879176

DATABASE_URL_OLD = "postgresql://postgres.qtkrrwtorkmfhxakemjp:ANEES879176@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

def test_old_connection():
    try:
        print(f"Connecting to OLD Database ({DATABASE_URL_OLD.split('@')[1]})...")
        conn = psycopg2.connect(DATABASE_URL_OLD)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[SUCCESS] Connection Successful to OLD DB!")
        print(f"Version: {version[0]}")
        
        # Check user count to verify we have data
        cursor.execute("SELECT count(*) FROM users;")
        count = cursor.fetchone()[0]
        print(f"Found {count} users in old database.")

        # Get column names
        cursor.execute("SELECT * FROM users LIMIT 1;")
        col_names = [desc[0] for desc in cursor.description]
        print(f"User Columns: {col_names}")
        
        conn.close()
    except Exception as e:
        print(f"[ERROR] Connection Failed: {e}")

if __name__ == "__main__":
    test_old_connection()
