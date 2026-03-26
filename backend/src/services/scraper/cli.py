#!/usr/bin/env python3
"""
cli.py - VECINA Data Scraping & Loading Pipeline CLI

Orchestrator module for the VECINA data pipeline with enhanced logging.

Default mode: Additive. Adds new content without deleting old data.
Use --clean flag to wipe the database and start fresh.

Usage:
    python -m src.scraper.cli
    python -m src.scraper.cli --clean
    python -m src.scraper.cli --verbose
    python -m src.scraper.cli --clean --verbose

Or after installation:
    vecinita-scrape
    vecinita-scrape --clean
    vecinita-scrape --verbose
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import docker  # type: ignore[import-untyped]
from docker.errors import APIError, DockerException, NotFound  # type: ignore[import-untyped]
from dotenv import load_dotenv

# --- Color codes for terminal output ---


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    COLORS = {
        logging.DEBUG: Colors.OKBLUE,
        logging.INFO: Colors.OKGREEN,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.FAIL,
        logging.CRITICAL: Colors.FAIL + Colors.BOLD,
    }

    def format(self, record):
        # Add color to levelname
        if record.levelno in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelno]}{record.levelname}{Colors.ENDC}"
        return super().format(record)


# --- Configuration ---
class Config:
    """Pipeline configuration."""

    CHUNK_FILE = Path("data/new_content_chunks.txt")
    LINKS_FILE = Path("data/extracted_links.txt")
    MAIN_URL_FILE = Path("data/urls.txt")
    FAILED_URL_LOG = Path("data/failed_urls.txt")
    LOADER_SCRIPT = Path("src/utils/vector_loader.py")
    APP_CONTAINER_NAME = "vecinita-app"
    LOG_FILE = Path("vecinita_loader.log")

    # Database configuration - loaded from environment variables
    DB_HOST = os.getenv("DB_HOST", "db.dosbzlhijkeircyainwz.supabase.co")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    # REQUIRED: Must be set in .env file
    DB_PASSWORD = os.getenv("DB_PASSWORD")


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Set up logging with both console and file handlers.

    Args:
        verbose: If True, set console logging to DEBUG level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("vecinita_pipeline")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = ColoredFormatter("%(levelname)s | %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (always verbose)
    log_file = Path("logs")
    log_file.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(log_file / f"pipeline_{timestamp}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def print_section(message: str, logger: logging.Logger):
    """Print a section header."""
    separator = "=" * 70
    logger.info("")
    logger.info(f"{Colors.OKCYAN}{separator}{Colors.ENDC}")
    logger.info(f"{Colors.OKCYAN}{Colors.BOLD}{message}{Colors.ENDC}")
    logger.info(f"{Colors.OKCYAN}{separator}{Colors.ENDC}")


def run_command(cmd: list, logger: logging.Logger, description: str) -> tuple[bool, str]:
    """
    Run a shell command and log output.

    Args:
        cmd: Command as list of strings
        logger: Logger instance
        description: Description of what the command does

    Returns:
        Tuple of (success: bool, output: str)
    """
    logger.debug(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.stdout:
            logger.debug(f"Command output:\n{result.stdout}")

        logger.info(f"{Colors.OKGREEN}✓{Colors.ENDC} {description}")
        return True, result.stdout

    except subprocess.CalledProcessError as e:
        logger.error(f"{Colors.FAIL}✗{Colors.ENDC} {description} failed")
        logger.error(f"Error code: {e.returncode}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        return False, e.stderr

    except FileNotFoundError:
        logger.error(f"{Colors.FAIL}✗{Colors.ENDC} Command not found: {cmd[0]}")
        return False, "Command not found"


def clean_database(logger: logging.Logger, no_confirm: bool = False) -> bool:
    """
    Clean (truncate) the database tables.

    Args:
        logger: Logger instance
        no_confirm: If True, skip confirmation prompt

    Returns:
        True if successful, False otherwise
    """
    print_section("CLEANING DATABASE", logger)

    logger.warning("This will DELETE ALL DATA from the database!")

    # Confirm with user (unless no_confirm is set)
    if not no_confirm:
        try:
            response = input(
                f"{Colors.WARNING}Are you sure you want to continue? (y/n): {Colors.ENDC}"
            )
            if response.lower() not in ["y", "yes"]:
                logger.info("Operation cancelled by user.")
                return False
        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user.")
            return False
    else:
        logger.info("Skipping confirmation (--no-confirm flag set)")

    # Use Python database CLI instead of psql
    cmd = [
        sys.executable,
        "-m",
        "src.agent.utils.db_cli",
        "truncate",
        "--no-confirm",  # We already confirmed above
    ]

    success, _ = run_command(cmd, logger, "Database truncated")
    return success


def clean_old_files(logger: logging.Logger) -> bool:
    """
    Clean old log and chunk files.

    Args:
        logger: Logger instance

    Returns:
        True if successful
    """
    print_section("CLEANING OLD LOG/CHUNK FILES", logger)

    files_to_clean = [
        Config.CHUNK_FILE,
        Config.FAILED_URL_LOG,
        Config.LINKS_FILE,
        Config.LOG_FILE,
    ]

    cleaned_count = 0
    for file_path in files_to_clean:
        if file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"Deleted: {file_path}")
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
        else:
            logger.debug(f"File doesn't exist (skip): {file_path}")

    # Create empty chunk file
    try:
        Config.CHUNK_FILE.parent.mkdir(parents=True, exist_ok=True)
        Config.CHUNK_FILE.touch()
        logger.info(f"{Colors.OKGREEN}✓{Colors.ENDC} Cleaned {cleaned_count} old files")
        logger.info(f"{Colors.OKGREEN}✓{Colors.ENDC} Created new empty chunk file")
        return True
    except Exception as e:
        logger.error(f"Failed to create chunk file: {e}")
        return False


def run_initial_scrape(
    logger: logging.Logger, use_stream: bool = False, debug: bool = False
) -> bool:
    """
    Run the initial scraping with standard loaders.

    Args:
        logger: Logger instance
        use_stream: If True, upload chunks immediately (streaming mode)
        debug: If True, save chunks to local file

    Returns:
        True if successful, False otherwise
    """
    print_section("RUNNING INITIAL SCRAPE", logger)

    if not Config.MAIN_URL_FILE.exists():
        logger.error(f"URL file not found: {Config.MAIN_URL_FILE}")
        return False

    # Count URLs to process
    try:
        with open(Config.MAIN_URL_FILE, encoding="utf-8") as f:
            url_count: int | str = sum(1 for line in f if line.strip() and not line.startswith("#"))
        logger.info(f"Processing {url_count} URLs from {Config.MAIN_URL_FILE}")
    except Exception as e:
        logger.warning(f"Could not count URLs: {e}")
        url_count = "unknown"

    # Run scraper directly (imported) instead of subprocess for better logging
    try:
        from pathlib import Path

        from src.services.scraper.scraper import VecinaScraper

        logger.info(f"{Colors.OKCYAN}Initializing scraper...{Colors.ENDC}")

        # Prepare output file path (or None if not debugging)
        output_file = str(Config.CHUNK_FILE)

        # Initialize scraper
        scraper = VecinaScraper(
            output_file=output_file,
            failed_log=str(Config.FAILED_URL_LOG),
            links_file=str(Config.LINKS_FILE),
            stream_mode=use_stream,
        )

        logger.info(f"{Colors.OKGREEN}Scraper initialized successfully{Colors.ENDC}")

        # Read URLs
        try:
            with open(Config.MAIN_URL_FILE, encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            logger.debug(f"Read {len(urls)} URLs from file")
        except Exception as e:
            logger.error(f"Failed to read URL file: {e}")
            return False

        if not urls:
            logger.warning("No URLs to process")
            return True

        # Run scraper
        logger.info(f"{Colors.OKCYAN}Starting scraping process...{Colors.ENDC}")
        total, successful, failed = scraper.scrape_urls(urls)

        # Print summary and finalize
        scraper.print_summary()
        scraper.finalize()

        logger.info(f"{Colors.OKGREEN}Initial scrape completed{Colors.ENDC}")

        # Log statistics
        if debug and output_file and Path(output_file).exists():
            try:
                chunk_size = Path(output_file).stat().st_size
                logger.info(f"Chunk file size: {chunk_size:,} bytes")
            except Exception as e:
                logger.debug(f"Could not get chunk file stats: {e}")

        return True

    except Exception as e:
        logger.error(f"{Colors.FAIL}Scraper error: {e}{Colors.ENDC}")
        logger.exception("Full traceback:")
        return False


def rerun_failed_urls(
    logger: logging.Logger, use_stream: bool = False, debug: bool = False
) -> bool:
    """
    Re-run failed URLs with Playwright loader.

    Args:
        logger: Logger instance
        use_stream: If True, upload chunks immediately (streaming mode)
        debug: If True, save chunks to local file

    Returns:
        True if successful or no failed URLs, False if re-run failed
    """
    print_section("RE-RUNNING FAILED URLS WITH PLAYWRIGHT", logger)

    if not Config.FAILED_URL_LOG.exists():
        logger.info("No failed URLs log found. Skipping re-run.")
        return True

    # Check if file has content
    try:
        with open(Config.FAILED_URL_LOG, encoding="utf-8") as f:
            failed_urls = [line.strip() for line in f if line.strip()]

        if not failed_urls:
            logger.info("No failed URLs found. Skipping re-run.")
            return True

        logger.info(f"Found {len(failed_urls)} failed URLs. Re-running with Playwright...")
        logger.debug(f"Failed URLs: {failed_urls[:5]}{'...' if len(failed_urls) > 5 else ''}")

    except Exception as e:
        logger.error(f"Could not read failed URLs log: {e}")
        return False

    # Run scraper directly instead of subprocess for better logging
    try:
        from src.services.scraper.scraper import VecinaScraper

        logger.info(f"{Colors.OKCYAN}Initializing Playwright scraper...{Colors.ENDC}")

        # Prepare output file path (or None if not debugging)
        output_file = str(Config.CHUNK_FILE)

        # Initialize scraper with Playwright forced
        scraper = VecinaScraper(
            output_file=output_file,
            failed_log=str(Config.FAILED_URL_LOG),
            links_file=str(Config.LINKS_FILE),
            stream_mode=use_stream,
        )

        logger.info(f"{Colors.OKGREEN}Scraper initialized{Colors.ENDC}")

        # Run with Playwright forced
        logger.info(f"{Colors.OKCYAN}Starting Playwright re-run...{Colors.ENDC}")
        total, successful, failed = scraper.scrape_urls(failed_urls, force_loader="playwright")

        # Print summary and finalize
        scraper.print_summary()
        scraper.finalize()

        logger.info(f"{Colors.OKGREEN}Playwright re-run completed{Colors.ENDC}")

        # Report final failed count
        if Config.FAILED_URL_LOG.exists():
            try:
                with open(Config.FAILED_URL_LOG, encoding="utf-8") as f:
                    final_failed = sum(1 for line in f if line.strip())
                if final_failed > 0:
                    logger.warning(f"{final_failed} URLs still failed after Playwright re-run")
                else:
                    logger.info("All URLs processed successfully!")
            except Exception as e:
                logger.debug(f"Could not count final failed URLs: {e}")

        return True

    except Exception as e:
        logger.error(f"{Colors.FAIL}Playwright re-run error: {e}{Colors.ENDC}")
        logger.exception("Full traceback:")
        return False


def load_data_to_database(logger: logging.Logger) -> bool:
    """
    Load processed chunks into the vector database.

    Args:
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    print_section("LOADING NEW DATA INTO DATABASE", logger)

    if not Config.CHUNK_FILE.exists():
        logger.error(f"Chunk file not found: {Config.CHUNK_FILE}")
        return False

    # Check if chunk file has content
    try:
        chunk_size = Config.CHUNK_FILE.stat().st_size
        if chunk_size == 0:
            logger.warning("Chunk file is empty. Nothing to load.")
            return False
        logger.info(f"Loading {chunk_size:,} bytes of data...")
    except Exception as e:
        logger.warning(f"Could not check chunk file: {e}")

    cmd = [
        sys.executable,
        str(Config.LOADER_SCRIPT),
        str(Config.CHUNK_FILE),
    ]

    success, _ = run_command(cmd, logger, "Data loaded into database")
    return success


def restart_application(logger: logging.Logger) -> bool:
    """
    Restart the Docker application container, or start it if not running.
    Uses Docker Python SDK for better error handling and control.

    Args:
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    print_section("RESTARTING APPLICATION", logger)

    try:
        # Initialize Docker client
        client = docker.from_env()

        # Verify Docker is running by pinging
        client.ping()
        logger.debug("Docker connection established")

    except DockerException as e:
        logger.warning("Docker Engine is not running or not accessible.")
        logger.info("Please start Docker Desktop and run 'docker-compose up -d' manually.")
        logger.debug(f"Docker error: {e}")
        return True  # Non-critical, return True to continue pipeline

    try:
        # Try to get the container
        container = client.containers.get(Config.APP_CONTAINER_NAME)
        logger.debug(f"Found container '{Config.APP_CONTAINER_NAME}'")

        # Check container status
        container.reload()  # Refresh container state
        status = container.status

        if status == "running":
            logger.info("Container is running. Restarting...")
            container.restart()
            logger.info(
                f"{Colors.OKGREEN}✓{Colors.ENDC} Container '{Config.APP_CONTAINER_NAME}' restarted successfully"
            )
        elif status in ["exited", "created", "paused"]:
            logger.info(f"Container status: {status}. Starting...")
            container.start()
            logger.info(
                f"{Colors.OKGREEN}✓{Colors.ENDC} Container '{Config.APP_CONTAINER_NAME}' started successfully"
            )
        else:
            logger.warning(f"Container status: {status}. Manual intervention may be required.")
            return True

        return True

    except NotFound:
        # Container doesn't exist, try docker-compose
        logger.info(f"Container '{Config.APP_CONTAINER_NAME}' not found.")
        logger.info("Attempting to start with docker-compose...")

        # Fall back to subprocess for docker-compose
        compose_cmd = "docker-compose" if shutil.which("docker-compose") else "docker compose"
        start_cmd = compose_cmd.split() + ["up", "-d", "app"]

        try:
            subprocess.run(start_cmd, capture_output=True, text=True, check=True)
            logger.info(
                f"{Colors.OKGREEN}✓{Colors.ENDC} Container started successfully with docker-compose"
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to start container with docker-compose.")
            logger.info("You may need to run 'docker-compose up -d' manually.")
            logger.debug(f"Error: {e.stderr}")
            return True  # Non-critical

    except APIError as e:
        logger.error(f"Docker API error: {e}")
        logger.info("Please check Docker Desktop and try 'docker-compose up -d' manually.")
        return True  # Non-critical

    except Exception as e:
        logger.error(f"Unexpected error managing container: {e}")
        logger.debug("Traceback:", exc_info=True)
        return True  # Non-critical

    finally:
        try:
            client.close()
        except Exception:
            pass


def print_summary(logger: logging.Logger, start_time: datetime):
    """
    Print pipeline execution summary.

    Args:
        logger: Logger instance
        start_time: Pipeline start time
    """
    print_section("PIPELINE COMPLETE!", logger)

    # Calculate duration
    duration = datetime.now() - start_time
    minutes = int(duration.total_seconds() // 60)
    seconds = int(duration.total_seconds() % 60)

    logger.info(f"Total execution time: {minutes}m {seconds}s")
    logger.info("")

    # File locations
    if Config.CHUNK_FILE.exists():
        chunk_size = Config.CHUNK_FILE.stat().st_size
        logger.info(
            f"{Colors.OKGREEN}✓{Colors.ENDC} Chunks saved to: {Config.CHUNK_FILE} ({chunk_size:,} bytes)"
        )

    if Config.LINKS_FILE.exists():
        link_count = sum(1 for _ in open(Config.LINKS_FILE))
        logger.info(
            f"{Colors.OKGREEN}✓{Colors.ENDC} Links saved to: {Config.LINKS_FILE} ({link_count} links)"
        )

    if Config.FAILED_URL_LOG.exists():
        failed_count = sum(1 for line in open(Config.FAILED_URL_LOG) if line.strip())
        if failed_count > 0:
            logger.warning(f"Failed URLs logged to: {Config.FAILED_URL_LOG} ({failed_count} URLs)")
        else:
            logger.info(f"{Colors.OKGREEN}✓{Colors.ENDC} No failed URLs!")

    # Log file location
    log_files = list(Path("logs").glob("pipeline_*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"{Colors.OKBLUE}ℹ{Colors.ENDC} Detailed log: {latest_log}")


def main():
    """Main pipeline execution."""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="VECINA data scraping and loading pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vecinita-scrape                   # Run in additive mode (file-based)
  vecinita-scrape --clean           # Clean database first
  vecinita-scrape --stream          # Streaming mode (memory-efficient)
  vecinita-scrape --clean --stream  # Clean + streaming
  vecinita-scrape --verbose         # Verbose output
        """,
    )

    parser.add_argument(
        "--clean", action="store_true", help="Clean (truncate) database before loading new data"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose (DEBUG) logging"
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode: upload chunks immediately during scraping (reduces memory usage, skips file I/O)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode: save chunks to local file and verbose logging",
    )

    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts (use with caution with --clean)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)
    start_time = datetime.now()

    # Print header
    logger.info("")
    logger.info(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    logger.info(f"{Colors.BOLD}{Colors.HEADER}VECINA Data Scraping & Loading Pipeline{Colors.ENDC}")
    logger.info(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    logger.info(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.clean:
        logger.info(f"Mode: {Colors.WARNING}CLEAN (database will be truncated){Colors.ENDC}")
    else:
        logger.info(f"Mode: {Colors.OKGREEN}ADDITIVE (new content will be added){Colors.ENDC}")

    if args.stream:
        logger.info(
            f"Streaming: {Colors.OKCYAN}ENABLED (chunks uploaded immediately, reduced memory usage){Colors.ENDC}"
        )
    else:
        logger.info("Streaming: OFF (traditional file-based processing)")

    if args.debug:
        logger.info(f"Debug: {Colors.OKCYAN}ENABLED (chunks saved to local file){Colors.ENDC}")
    else:
        logger.info("Debug: OFF (no local chunk files saved)")

    logger.info("")

    # Pipeline execution
    try:
        # Step 1: Clean database if requested
        if args.clean:
            if not clean_database(logger, no_confirm=args.no_confirm):
                logger.error("Database cleaning failed or cancelled. Exiting.")
                sys.exit(1)

        # Step 2: Clean old files (only if debug mode)
        if args.debug:
            if not clean_old_files(logger):
                logger.error("Failed to clean old files. Exiting.")
                sys.exit(1)

        # Step 3: Run initial scrape
        if not run_initial_scrape(logger, use_stream=args.stream, debug=args.debug):
            logger.error("Initial scrape failed. Exiting.")
            sys.exit(1)

        # Step 4: Re-run failed URLs with Playwright
        if not rerun_failed_urls(logger, use_stream=args.stream, debug=args.debug):
            logger.error("Playwright re-run failed. Exiting.")
            sys.exit(1)

        # Step 5: Load data into database (skip in streaming mode - already uploaded)
        if args.stream:
            logger.info(
                f"{Colors.OKCYAN}Skipping data loading step (streaming mode - data already uploaded){Colors.ENDC}"
            )
        elif args.debug:
            if not load_data_to_database(logger):
                logger.error("Data loading failed. Exiting.")
                sys.exit(1)

        # Step 6: Restart application
        if not restart_application(logger):
            logger.warning("Application restart failed, but pipeline completed.")

        # Print summary
        print_summary(logger, start_time)

        logger.info("")
        logger.info(f"{Colors.OKGREEN}{Colors.BOLD}✓ Pipeline completed successfully!{Colors.ENDC}")
        logger.info("")

    except KeyboardInterrupt:
        logger.info("")
        logger.warning("Pipeline interrupted by user.")
        sys.exit(130)

    except Exception as e:
        logger.error("")
        logger.error(f"{Colors.FAIL}Pipeline failed with unexpected error:{Colors.ENDC}")
        logger.error(f"{Colors.FAIL}{e}{Colors.ENDC}")
        logger.exception("Traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
