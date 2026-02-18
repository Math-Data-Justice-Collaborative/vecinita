#!/usr/bin/env python3
"""
Database CLI Utility for Vecinita

Provides command-line interface for database operations without requiring psql.
Uses psycopg2 for direct PostgreSQL connections.

Usage:
    python -m src.utils.db_cli truncate
    python -m src.utils.db_cli stats
    python -m src.utils.db_cli test-connection
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


# --- Configuration ---
class DBConfig:
    """Database configuration from environment variables."""

    @staticmethod
    def get_connection_params() -> Dict[str, Any]:
        """Get database connection parameters from environment or defaults."""
        # Try to get from environment first
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            # Parse DATABASE_URL if provided
            return {'dsn': database_url}

        # Fall back to individual parameters
        return {
            'host': os.getenv('DB_HOST', 'db.dosbzlhijkeircyainwz.supabase.co'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            # REQUIRED: Must be set in .env file
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require'),
        }


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('db_cli')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('%(levelname)s | %(message)s')
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


def get_connection():
    """
    Create and return a database connection.

    Returns:
        psycopg2 connection object

    Raises:
        psycopg2.Error: If connection fails
    """
    params = DBConfig.get_connection_params()

    if 'dsn' in params:
        conn = psycopg2.connect(params['dsn'])
    else:
        conn = psycopg2.connect(**params)

    return conn


def test_connection(logger: logging.Logger) -> bool:
    """
    Test database connection.

    Args:
        logger: Logger instance

    Returns:
        True if connection successful, False otherwise
    """
    logger.info("Testing database connection...")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        logger.info("✓ Connection successful")
        logger.info(f"PostgreSQL version: {version.split(',')[0]}")
        return True

    except psycopg2.Error as e:
        logger.error(f"✗ Connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def truncate_tables(logger: logging.Logger, tables: Optional[list] = None) -> bool:
    """
    Truncate specified tables (delete all data).

    Args:
        logger: Logger instance
        tables: List of table names to truncate. If None, uses default tables.

    Returns:
        True if successful, False otherwise
    """
    if tables is None:
        tables = [
            'public.document_chunks',
            'public.search_queries',
            'public.processing_queue'
        ]

    logger.info(f"Truncating tables: {', '.join(tables)}")
    logger.warning("This will DELETE ALL DATA from these tables!")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Truncate all tables in one command
        table_list = ', '.join(tables)
        truncate_sql = f"TRUNCATE TABLE {table_list} CASCADE;"

        logger.debug(f"Executing: {truncate_sql}")
        cursor.execute(truncate_sql)
        conn.commit()

        cursor.close()
        conn.close()

        logger.info("✓ Tables truncated successfully")
        return True

    except psycopg2.Error as e:
        logger.error(f"✗ Truncate failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def get_table_stats(logger: logging.Logger) -> bool:
    """
    Get statistics for main tables.

    Args:
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("Fetching table statistics...")

    tables = [
        'document_chunks',
        'search_queries',
        'processing_queue'
    ]

    try:
        conn = get_connection()
        cursor = conn.cursor()

        logger.info("")
        logger.info("=" * 60)
        logger.info("TABLE STATISTICS")
        logger.info("=" * 60)

        for table in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM public.{table};")
            count = cursor.fetchone()[0]

            # Get table size
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_total_relation_size('public.{table}'));
            """)
            size = cursor.fetchone()[0]

            logger.info(f"{table:25s} | {count:>10,} rows | {size:>10s}")

        logger.info("=" * 60)

        # Get total database size
        cursor.execute(
            "SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()[0]
        logger.info(f"Total database size: {db_size}")
        logger.info("")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        logger.error(f"✗ Failed to get stats: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def vacuum_analyze(logger: logging.Logger) -> bool:
    """
    Run VACUUM ANALYZE on the database to optimize performance.

    Args:
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("Running VACUUM ANALYZE...")

    try:
        conn = get_connection()
        conn.set_isolation_level(
            psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("VACUUM ANALYZE;")

        cursor.close()
        conn.close()

        logger.info("✓ VACUUM ANALYZE completed")
        return True

    except psycopg2.Error as e:
        logger.error(f"✗ VACUUM ANALYZE failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def list_tables(logger: logging.Logger) -> bool:
    """
    List all tables in the public schema.

    Args:
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    logger.info("Listing tables in public schema...")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()

        logger.info("")
        logger.info("=" * 60)
        logger.info("TABLES IN PUBLIC SCHEMA")
        logger.info("=" * 60)

        for i, (table,) in enumerate(tables, 1):
            logger.info(f"{i:2d}. {table}")

        logger.info("=" * 60)
        logger.info(f"Total: {len(tables)} tables")
        logger.info("")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        logger.error(f"✗ Failed to list tables: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Database CLI utility for Vecinita',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  test-connection   Test database connection
  truncate          Truncate main tables (delete all data)
  stats             Show table statistics
  vacuum            Run VACUUM ANALYZE to optimize database
  list-tables       List all tables in public schema

Examples:
  python -m src.utils.db_cli test-connection
  python -m src.utils.db_cli truncate
  python -m src.utils.db_cli stats
  python -m src.utils.db_cli vacuum
  python -m src.utils.db_cli list-tables -v
        """
    )

    parser.add_argument(
        'command',
        choices=['test-connection', 'truncate',
                 'stats', 'vacuum', 'list-tables'],
        help='Command to execute'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--tables',
        nargs='+',
        help='Specific tables to operate on (for truncate command)'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt (for truncate command)'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

    # Execute command
    success = False

    try:
        if args.command == 'test-connection':
            success = test_connection(logger)

        elif args.command == 'truncate':
            # Confirmation prompt
            if not args.no_confirm:
                logger.warning("This will DELETE ALL DATA from the tables!")
                response = input("Are you sure you want to continue? (y/n): ")
                if response.lower() not in ['y', 'yes']:
                    logger.info("Operation cancelled.")
                    sys.exit(0)

            success = truncate_tables(logger, args.tables)

        elif args.command == 'stats':
            success = get_table_stats(logger)

        elif args.command == 'vacuum':
            success = vacuum_analyze(logger)

        elif args.command == 'list-tables':
            success = list_tables(logger)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
