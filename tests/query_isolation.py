#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VECINITA-RIOS: Query Endpoint Isolation Probe
Path: tests/query_isolation.py

Diagnostic script to isolate the RAG pipeline.
"""

import os
import sys
import logging
import argparse
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_isolation_test(verbose=False):
    load_dotenv()
    
    print("\n" + "="*60)
    print("VECINITA-RIOS: ISOLATION PROBE")
    print("="*60)

    # --- PHASE 1: ENVIRONMENT ---
    print(f"\n[PHASE 1] Environment & Secrets")
    conn_str = os.getenv("SUPABASE_CONN_STR")
    api_key = os.getenv("OPENAI_API_KEY")
    
    status_env = "✅" if (conn_str and api_key) else "❌"
    print(f"{status_env} SUPABASE_CONN_STR: {'Found' if conn_str else 'MISSING'}")
    print(f"{status_env} OPENAI_API_KEY: {'Found' if api_key else 'MISSING'}")
    
    if not (conn_str and api_key):
        return False

    # --- PHASE 2: EMBEDDINGS ---
    print(f"\n[PHASE 2] OpenAI Embedding Object Initialization")
    try:
        # Targeting the 3072 dimension model
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        test_vector = embeddings.embed_query("Providence health resources")
        print(f"✅ LangChain Object created successfully.")
        print(f"✅ Vector generation successful. Dimensions: {len(test_vector)}")
    except Exception as e:
        print(f"❌ ERROR in Phase 2: {e}")
        return False

    # --- PHASE 3: DATABASE HANDSHAKE ---
    print(f"\n[PHASE 3] SQLAlchemy Connection")
    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            print(f"✅ Connection to Supabase established.")
    except Exception as e:
        print(f"❌ ERROR in Phase 3: {e}")
        return False

    # --- PHASE 4: VECTOR FUNCTION EXECUTION ---
    print(f"\n[PHASE 4] RPC Function: search_similar_documents")
    try:
        with engine.connect() as conn:
            query_sql = text("""
                SELECT content, source_url, similarity 
                FROM search_similar_documents(
                    query_embedding := :emb,
                    match_threshold := 0.1,
                    match_count := 3
                )
            """)
            result = conn.execute(query_sql, {"emb": test_vector})
            rows = result.fetchall()
            
            if rows:
                print(f"✅ SUCCESS! Retrieved {len(rows)} relevant chunks.")
                for i, row in enumerate(rows):
                    print(f"   {i+1}. [{row[1]}] (Score: {round(row[2], 4)})")
            else:
                print("⚠️  Database responded but returned 0 matches.")
                
    except Exception as e:
        print(f"❌ ERROR in Phase 4: {e}")
        return False

    print("\n" + "="*60)
    print("RESULT: SYSTEM IS GREEN")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vecinita Isolation Probe")
    parser.add_argument("--verbose", action="store_true", help="Increase output verbosity")
    args = parser.parse_args()
    
    success = run_isolation_test(verbose=args.verbose)
    sys.exit(0 if success else 1)
