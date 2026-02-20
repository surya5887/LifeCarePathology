import os
import psycopg2
from urllib.parse import urlparse

# URL from config.py
DATABASE_URL = "postgresql://postgres.qtkrrwtorkmfhxakemjp:ANEES879176@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

def verify_tables():
    try:
        # Parse URL
        result = urlparse(DATABASE_URL)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port

        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        cursor = conn.cursor()

        print("Checking tables in database...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\nExisting Tables:")
        found_blocked_slots = False
        for table in tables:
            print(f"- {table[0]}")
            if table[0] == 'blocked_slots':
                found_blocked_slots = True
        
        if found_blocked_slots:
            print("\n✅ SUCCESS: 'blocked_slots' table found!")
        else:
            print("\n❌ FAILURE: 'blocked_slots' table NOT found!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_tables()
