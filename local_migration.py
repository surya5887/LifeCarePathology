
import psycopg2
from psycopg2 import sql

# =================CONFIGURATION=================

# 1. SOURCE: Old Database (Verified Working with URI in test_old_db.py)
# Project: qtkrrwtorkmfhxakemjp
# Host: aws-1-ap-southeast-1.pooler.supabase.com (Verified)
# Added sslmode=require to ensure connection
OLD_DB_URL = "postgresql://postgres.qtkrrwtorkmfhxakemjp:ANEES879176@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

# 2. TARGET: New Database
# Project: cvuvtnnpxjpjxndaqask
# User: postgres.cvuvtnnpxjpjxndaqask
# Password: Cyy?Ug2DS_Zj@+q  ->  Cyy%3FUg2DS_Zj%40%2Bq (Manually encoded)
# Host: aws-1... (Assuming correct pooler since aws-0 failed with 'Tenant not found')
NEW_DB_URL = "postgresql://postgres.cvuvtnnpxjpjxndaqask:Cyy%3FUg2DS_Zj%40%2Bq@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

# ===============================================

def get_connection(url):
    print(f"Connecting to {url.split('@')[1].split('?')[0]}...", flush=True)
    return psycopg2.connect(url)

def migrate():
    try:
        # Connect to Source
        print("\n🔌 Connecting to OLD Database...", flush=True)
        conn_old = get_connection(OLD_DB_URL)
        cur_old = conn_old.cursor()
        print("✅ Connected to OLD Database.")

        # Connect to Target
        print("\n🔌 Connecting to NEW Database...")
        try:
            conn_new = get_connection(NEW_DB_URL)
        except Exception as e:
            print(f"⚠️ Failed to connect to New DB on aws-1: {e}")
            print("   (Trying aws-0 as fallback locally if aws-1 fails?)")
            raise e

        cur_new = conn_new.cursor()
        print("✅ Connected to NEW Database.")

        # Tables to Migrate
        tables = ['users', 'test_parameters', 'bookings', 'contact_messages', 'reports']
        
        print("\n🧹 Truncating NEW Database tables...")
        cur_new.execute("TRUNCATE TABLE users, test_parameters, bookings, contact_messages, reports CASCADE;")
        conn_new.commit()
        print("✅ Tables truncated.")

        for table in tables:
            print(f"\n📦 Migrating table: {table}")
            
            try:
                # Fetch from Old
                cur_old.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))
                rows = cur_old.fetchall()
                
                if not rows:
                    print(f"   -> No data in {table}. Skipping.")
                    continue
                
                # Get Columns
                col_names = [desc[0] for desc in cur_old.description]
                columns = sql.SQL(", ").join(map(sql.Identifier, col_names))
                
                # Insert into New
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table),
                    columns,
                    sql.SQL(", ").join(sql.SQL("%s") for _ in col_names)
                )
                
                print(f"   -> Inserting {len(rows)} rows...")
                cur_new.executemany(query, rows)
                conn_new.commit()
                print(f"   -> ✅ Success: {len(rows)} rows migrated.")
                
            except Exception as e:
                conn_new.rollback()
                print(f"   -> ❌ Failed to migrate {table}: {e}")

        print("\n🎉 MIGRATION COMPLETE!")
        conn_old.close()
        conn_new.close()

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    migrate()
