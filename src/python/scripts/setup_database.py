"""
Set up the database schema for auto-osint.

Creates every table declared on the shared declarative Base, using
DATABASE_URL when set (SQLite by default for local development).
"""

import os
import sys
from pathlib import Path

# Make `src.python` importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from dotenv import load_dotenv

from src.python import models  # noqa: F401  (import registers model tables)
from src.python.database import DEFAULT_DATABASE_URL, create_db_engine, init_db
from src.python.models.base import Base


def setup_database(url: str | None = None):
    """Create the schema and report where it landed."""
    load_dotenv()
    resolved_url = url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL

    engine = create_db_engine(resolved_url)
    init_db(engine)

    print("Database schema created successfully")
    print(f"Database location: {resolved_url}")
    print(f"Tables: {', '.join(sorted(Base.metadata.tables))}")
    return engine


def main(argv: list[str] | None = None) -> int:
    """
    Console entry point: create the schema and return an exit status.

    setup_database() returns an Engine, which must not leak into sys.exit()
    (a non-int return value makes the process exit 1).
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="auto-osint-db", description="Create the auto-osint database schema."
    )
    parser.add_argument("--url", default=None, help="Database URL to create")
    args = parser.parse_args(argv)

    setup_database(args.url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
