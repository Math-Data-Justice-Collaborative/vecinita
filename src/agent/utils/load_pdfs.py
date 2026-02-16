# ############################################################################
# FILE: load_pdfs.py
# PATH: src/agent/utils/load_pdfs.py
# ROLE: Data Ingestion & Local Embedding Engine
# DESCRIPTION: Orchestrates the transition of raw text data into the 384-dim
#              Supabase vector store. It utilizes the LocalHFProvider to 
#              ensure data alignment with the Sovereign local worker.
# ############################################################################

import os
import glob
import logging
from supabase import create_client
from src.agent.tools.embedders.local_hf_provider import LocalHFProvider

# Configure logging for better observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vecinita.loader")

def ingest_data():
    """
    Main ingestion loop. Searches for .txt scrapes, chunks them,
    generates 384-dim embeddings locally, and uploads to Supabase.
    """
    # 1. Environment Setup
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        logger.error("Environment variables SUPABASE_URL or SERVICE_KEY missing.")
        return
        
    supabase = create_client(url, key)
    embedder = LocalHFProvider()
    
    # 2. Define the path inside the container (mounted from src/agent/data)
    data_path = "/app/src/agent/data/manual_scraping/*.txt"
    files = glob.glob(data_path)
    
    if not files:
        logger.warning(f"No files found at {data_path}. Ensure folder is mounted.")
        return

    logger.info(f"🚀 Found {len(files)} files. Starting 384-dim ingestion.")

    for file_path in files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Semantic Chunking: 1200 chars (~300 words) for high context retention
                chunks = [content[i:i+1200] for i in range(0, len(content), 1200)]
                
                for i, chunk in enumerate(chunks):
                    # Local Inference (The Sovereign Brain)
                    vector = embedder.embed_query(chunk)
                    
                    # Database Record Persistence
                    supabase.table("documents").insert({
                        "content": chunk,
                        "metadata": {"source": filename, "chunk": i},
                        "embedding": vector
                    }).execute()
                    
                    logger.info(f"✅ Indexed {filename} - Chunk {i}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to process {filename}: {str(e)}")

    logger.info("================================================")
    logger.info("🏁 ALL DATA ALIGNED AND INDEXED")
    logger.info("================================================")

if __name__ == "__main__":
    ingest_data()

# ############################################################################
# END OF FILE: load_pdfs.py
# ############################################################################
