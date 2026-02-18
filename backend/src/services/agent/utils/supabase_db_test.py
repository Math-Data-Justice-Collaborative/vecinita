##Filename: supabase_db_test.py
# A simple script to test the connection to a Supabase database.
# It loads credentials from a .env file, creates a client,
# and attempts to fetch one row from a specified table.

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from a .env file in the same directory
load_dotenv()

print("--- Starting database connection test ---")

# --- Configuration ---
# This MUST be a real table that exists in your Supabase project.
# We are using "document_chunks" because we know it exists.
TABLE_TO_QUERY = "document_chunks"

# 1. Load credentials from environment variables
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# 2. Check if the environment variables were loaded
if not supabase_url or not supabase_key:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    print("Ensure you have a .env file in the same directory with these values.")
    exit(1)

print("✅ Credentials loaded from environment.")

try:
    # 3. Create the Supabase client
    print(f"Attempting to connect to Supabase URL: {supabase_url[:25]}...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client created successfully.")

    # 4. Perform a simple query to test the connection
    print(f"Attempting to query table: '{TABLE_TO_QUERY}'...")
    response = supabase.table(TABLE_TO_QUERY).select("*").limit(1).execute()
    
    # 5. Check the response and print the result
    print("✅ Query executed successfully!")
    print("\n--- TEST SUCCEEDED ---")
    print("Data received:", response.data)

except Exception as e:
    print("\n--- ❌ TEST FAILED ---")
    print("An error occurred:", e)
    exit(1)

#--end-of-file
