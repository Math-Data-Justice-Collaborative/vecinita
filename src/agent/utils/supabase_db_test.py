## Filename: supabase_db_test.py
# Updated: 2026-02-09 - Rios VM Deployment Edition
# Purpose: Validates Supabase connection using the .env Single Source of Truth.

import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Force load the .env from the project root (absolute path)
env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"--- Starting database connection test (Source: {env_path}) ---")

# --- Configuration ---
TABLE_TO_QUERY = "document_chunks"

# 2. Load credentials
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# 3. Enhanced Key Validation
if not supabase_url or not supabase_key:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY not found in .env.")
    exit(1)

if supabase_key.startswith("sb_secret"):
    print("❌ ERROR: Your .env is using a Management Key (sb_secret...).")
    print("   Please use the Service Role JWT (starts with 'eyJ').")
    exit(1)

print("✅ Credentials found. Key format is valid (JWT).")

try:
    # 4. Create the Supabase client
    print(f"Connecting to: {supabase_url[:30]}...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client initialized.")

    # 5. Perform the query
    print(f"Checking table: '{TABLE_TO_QUERY}'...")
    response = supabase.table(TABLE_TO_QUERY).select("*").limit(1).execute()
    
    # 6. Final Result
    print("✅ Query successful!")
    print("\n--- TEST SUCCEEDED ---")
    if response.data:
        print(f"Data Sample: {str(response.data)[:100]}...")
    else:
        print("Note: Connection worked, but the table is currently empty.")

except Exception as e:
    print("\n--- ❌ TEST FAILED ---")
    print(f"Detailed Error: {e}")
    exit(1)
##END-OF-FILE
