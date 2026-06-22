#!/usr/bin/env python3
"""
scripts/init_db.py
One-time DB initialization script.
Run after first deploy or local setup.

Usage:
    python scripts/init_db.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting MediBook database initialization...")

    try:
        from database.db import create_database_if_not_exists, create_tables

        logger.info("Creating database if not exists...")
        create_database_if_not_exists()

        logger.info("Creating tables...")
        create_tables()

        logger.info("✅ Database initialization complete!")

    except ImportError as e:
        logger.error(f"Import error — check your PYTHONPATH: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("Check your DATABASE_URL or DB_* environment variables.")
        sys.exit(1)


if __name__ == "__main__":
    main()
