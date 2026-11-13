"""
Setup database schema for auto-osint.
Creates SQLite database with all required tables.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL (use SQLite for local development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///../../../data/auto_osint.db"
)

def setup_database():
    """Create database schema and tables."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Read SQL schema from file
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            with open(schema_file, "r") as f:
                schema_sql = f.read()
        else:
            # Define schema inline if file doesn't exist
            schema_sql = """
            -- Create tables
            CREATE TABLE IF NOT EXISTS investigation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_name TEXT NOT NULL,
                target_id TEXT,
                claim_under_investigation TEXT NOT NULL,
                status TEXT NOT NULL,
                stages_completed JSON,
                total_sources INTEGER DEFAULT 0,
                corroborated_sources INTEGER DEFAULT 0,
                contradictory_sources INTEGER DEFAULT 0,
                net_confidence_score REAL DEFAULT 0.0,
                investigation_notes TEXT,
                playbook_update TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claim TEXT NOT NULL,
                confidence REAL NOT NULL,
                independence_score REAL NOT NULL,
                independence_check_details JSON,
                corroborating_sources JSON,
                contradictions JSON,
                links JSON,
                chain_of_custody JSON,
                investigation_id INTEGER NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation (id)
            );

            CREATE TABLE IF NOT EXISTS openosint_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool TEXT NOT NULL,
                target TEXT NOT NULL,
                result JSON NOT NULL,
                source TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error TEXT,
                investigation_id INTEGER NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation (id)
            );

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_evidence_investigation_id ON evidence(investigation_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);
            CREATE INDEX IF NOT EXISTS idx_openosint_results_investigation_id ON openosint_results(investigation_id);
            """

        # Execute schema
        conn.execute(text(schema_sql))
        conn.commit()

        print("✅ Database schema created successfully")
        print(f"📊 Database location: {DATABASE_URL}")

if __name__ == "__main__":
    setup_database()
