#!/usr/bin/env python3
"""
VECINA Scraper CLI Entry Point

Usage:
    python -m src.utils.scraper.main --input <urls_file> --output-file <chunks_file> \
        --failed-log <failed_urls_file> [--links-file <links_file>] [--loader playwright|recursive|unstructured]
"""

import os
from pathlib import Path
import sys
import logging
import argparse
from importlib import import_module

# NOTE ON TESTABILITY:
# We intentionally use a direct import of VecinaScraper here instead of a dynamic
# import (e.g., via import_module) to keep the CLI entry point simple and avoid
# runtime import resolution issues when packaging or invoking via `python -m`.
#
# If tests need to substitute or mock the scraper implementation, they should
# patch this module-level name before calling `main()`, for example:
#     from backend.src.scraper import main
#     main.VecinaScraper = FakeScraper
#     main.main()
from .scraper import VecinaScraper


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


def main():
    """Main entry point for the scraper CLI."""
    parser = argparse.ArgumentParser(
        description="VECINA Scraper: Intelligent web scraper for community resources"
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="REQUIRED: Path to the input file of URLs to process (e.g., data/urls.txt)."
    )

    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="REQUIRED: Path to the output file for chunks. Content will be APPENDED."
    )

    parser.add_argument(
        "--failed-log",
        type=str,
        required=True,
        help="REQUIRED: Path to a file where failed URLs will be logged."
    )

    parser.add_argument(
        "--links-file",
        type=str,
        default=None,
        help="(Optional) Path to a file for saving extracted links and metadata."
    )

    parser.add_argument(
        "--loader",
        type=str,
        choices=['playwright', 'recursive', 'unstructured'],
        default=None,
        help="(Optional) Force a specific loader for all URLs in the input file."
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="(Optional) Enable streaming mode: upload chunks immediately to database (reduces memory usage)."
    )

    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.input):
        log.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Ensure output directory exists
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(args.failed_log).parent.mkdir(parents=True, exist_ok=True)

    if args.links_file:
        Path(args.links_file).parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Appending output to: {args.output_file}")

    # Log streaming mode
    if args.stream:
        log.info(
            "Streaming mode enabled: chunks will be uploaded immediately to database")

    # Initialize scraper
    try:
        scraper = VecinaScraper(
            output_file=args.output_file,
            failed_log=args.failed_log,
            links_file=args.links_file,
            stream_mode=args.stream
        )
    except Exception as e:
        log.error(f"Failed to initialize scraper: {e}")
        sys.exit(1)

    # Read URLs from input file
    try:
        # Try UTF-8 first, then fall back to UTF-8 with BOM, then latin-1
        encodings = ['utf-8', 'utf-8-sig', 'latin-1']
        urls = []
        decode_successful = False
        for encoding in encodings:
            try:
                with open(args.input, 'r', encoding=encoding) as f:
                    urls = [
                        line.strip().lstrip('\ufeff')
                        for line in f
                        if line.strip() and not line.startswith('#')
                    ]
                log.info(
                    f"Successfully read input file with {encoding} encoding")
                decode_successful = True
                break
            except UnicodeDecodeError:
                continue

        if not decode_successful:
            raise Exception(
                "Could not decode file with any supported encoding")

    except Exception as e:
        log.error(f"Failed to read input file {args.input}: {e}")
        sys.exit(1)

    if not urls:
        log.warning("No URLs found in input file.")
        sys.exit(0)

    log.info(f"Found {len(urls)} URLs to process.")

    # Scrape URLs
    try:
        total, successful, failed = scraper.scrape_urls(
            urls, force_loader=args.loader)
        scraper.print_summary()
        scraper.finalize()

        log.info(f"\n{'='*70}")
        log.info("SCRAPING PIPELINE COMPLETE!")
        log.info(f"{'='*70}")

    except KeyboardInterrupt:
        log.warning("\nScraping interrupted by user.")
        scraper.print_summary()
        sys.exit(130)
    except Exception as e:
        log.error(f"\nFatal error during scraping: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
