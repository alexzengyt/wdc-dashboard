import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
host = os.getenv("SUPABASE_HOST")
print("DEBUG host =", repr(host))

try:
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        dbname=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD"),  
        port=os.getenv("SUPABASE_PORT", 5432)
    )
    print("✅ Successfully connected to Supabase Postgres!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:")
    print(e)
