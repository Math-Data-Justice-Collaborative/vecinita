# utils/load_faq.py
import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
import logging

# --- CONFIGURATION ---
FAQ_FILE_PATH = "data/vecinita_faq.md"
TABLE_NAME = "curated_content"
# --- END CONFIGURATION ---

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def main():
    load_dotenv()
    supabase_url = os.environ.get("DATABASE_URL")  # Connect direct to DB
    if not supabase_url:
        raise ValueError("DATABASE_URL must be set in .env")

    # We use DATABASE_URL, which needs a different client init
    # Note: This uses postgres_client, not the full Supabase client
    from supabase.lib.client_options import ClientOptions
    supabase: Client = create_client(
        os.environ.get("SUPABASE_URL"),  # Needs this for auth
        os.environ.get("SUPABASE_KEY"),  # Needs this for auth
        options=ClientOptions(postgrest_client_timeout=10)
    )

    log.info(f"Connected to Supabase.")

    # 1. Initialize embedding model
    model_name = "sentence-transformers/all-mpnet-base-v2"
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    log.info(f"Embedding model loaded: {model_name}")

    # 2. Read and chunk the FAQ file
    try:
        with open(FAQ_FILE_PATH, 'r', encoding='utf-8') as f:
            faq_content = f.read()
    except FileNotFoundError:
        log.error(f"FATAL: FAQ file not found at {FAQ_FILE_PATH}")
        return
    except Exception as e:
        log.error(f"FATAL: Error reading file: {e}")
        return

    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(faq_content)
    log.info(f"Read and split {FAQ_FILE_PATH} into {len(chunks)} chunks.")

    # 3. Clear the old FAQs from the table
    log.info(f"Truncating (emptying) the '{TABLE_NAME}' table...")
    supabase.table(TABLE_NAME).delete().neq(
        'id', '00000000-0000-0000-0000-000000000000').execute()

    # 4. Generate embeddings and prepare data for upload
    log.info("Generating embeddings for new chunks...")
    data_to_upload = []
    for chunk in chunks:
        embedding = embedding_model.embed_query(chunk)
        data_to_upload.append({
            'content': chunk,
            'source': 'Vecinita FAQ',  # Set a clear source
            'embedding': embedding
        })

    # 5. Upload new chunks
    log.info(
        f"Uploading {len(data_to_upload)} new chunks to '{TABLE_NAME}'...")
    response = supabase.table(TABLE_NAME).insert(data_to_upload).execute()

    if len(response.data) == len(data_to_upload):
        log.info("✅ Successfully loaded all new FAQs into the database.")
    else:
        log.error(f"Upload may have failed. {response}")


if __name__ == "__main__":
    main()
