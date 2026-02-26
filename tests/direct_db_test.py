import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
# Using the direct connection string from your .env
db_url = os.getenv("SUPABASE_CONN_STR")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10;"))
        tables = [row[0] for row in result]
        print("\n" + "="*50)
        print("✅ DIRECT DATABASE CONNECTION SUCCESS!")
        print(f"Tables found: {tables}")
        print("="*50 + "\n")
except Exception as e:
    print(f"\n❌ Direct Connection Failed: {e}\n")
