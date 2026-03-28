#!/usr/bin/env python3
"""
Quick database cleaner + scraper loader for VECINA
No PowerShell or psql required!
"""

from src.scraper.uploader import DatabaseUploader
from src.scraper.main import main as scraper_main
from dotenv import load_dotenv
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env from project root (parent of backend)
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(str(env_file))
else:
    print(f"Warning: .env file not found at {env_file}")


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_database():
    """Truncate all documents from the database."""
    try:
        uploader = DatabaseUploader()
        logger.info("🗑️  Cleaning database...")

        # Delete all document chunks by querying all and deleting
        # First, get all IDs
        all_records = uploader.supabase_client.table(
            "document_chunks").select("id").execute()

        if all_records.data:
            # Delete all records
            response = uploader.supabase_client.table(
                "document_chunks").delete().gte("id", "00000000-0000-0000-0000-000000000000").execute()
            logger.info(
                f"✅ Database cleaned successfully - deleted {len(all_records.data)} records")
        else:
            logger.info("✅ Database already empty")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to clean database: {e}")
        return False


def check_database():
    """Check how many documents are in the database."""
    try:
        uploader = DatabaseUploader()
        response = uploader.supabase_client.table(
            "document_chunks").select("id").execute()
        count = len(response.data) if response.data else 0
        logger.info(f"📊 Database contains {count} documents")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to check database: {e}")
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean database and scrape URLs")
    parser.add_argument("--clean", action="store_true",
                        help="Clean database before scraping")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check database status")
    parser.add_argument("--input", default="../data/input/urls.txt",
                        help="URL file to scrape")
    parser.add_argument("--output", default="data/output/chunks.txt",
                        help="Output chunks file")
    parser.add_argument(
        "--failed", default="data/output/failed.txt", help="Failed URLs log")
    parser.add_argument("--stream", action="store_true",
                        help="Stream chunks to database")

    args = parser.parse_args()

    if args.check_only:
        check_database()
        sys.exit(0)

    if args.clean:
        logger.info("🧹 CLEAN MODE: Database will be truncated")
        confirm = input("Are you sure? (y/n): ")
        if confirm.lower() != "y":
            logger.info("Cancelled.")
            sys.exit(1)
        if not clean_database():
            sys.exit(1)

    # Check initial state
    initial_count = check_database()

    # Run scraper
    logger.info("🚀 Starting scraper...")
    sys.argv = [
        "src.scraper.main",
        "--input", args.input,
        "--output-file", args.output,
        "--failed-log", args.failed,
    ]
    if args.stream:
        sys.argv.append("--stream")

    try:
        scraper_main()
    except SystemExit:
        pass

    # Check final state
    final_count = check_database()
    logger.info(f"📈 Added {final_count - initial_count} documents to database")
    logger.info("✅ Done!")
