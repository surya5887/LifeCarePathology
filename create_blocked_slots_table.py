import os
import psycopg2
from urllib.parse import urlparse

# URL from config.py
DATABASE_URL = "postgresql://postgres.qtkrrwtorkmfhxakemjp:ANEES879176@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

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

        print("Attempting to create blocked_slots table...")
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS blocked_slots (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            time_slot VARCHAR(20),
            reason VARCHAR(200) DEFAULT 'Unavailable',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc')
        );
        """
        
        cursor.execute(create_table_query)
        print("Successfully created blocked_slots table (or it already existed).")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()
