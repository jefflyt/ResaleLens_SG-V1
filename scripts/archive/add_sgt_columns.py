"""Add started_at_sgt and completed_at_sgt columns to ingestion_runs table."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load env
env_local = Path(".env.local")
if env_local.exists():
    load_dotenv(env_local)
elif Path(".env").exists():
    load_dotenv(".env")

from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

engine = create_engine(database_url)

print("=" * 80)
print("📦 Adding SGT Timestamps Columns to ingestion_runs")
print("=" * 80)

with engine.connect() as conn:
    # Drop columns if they exist to reset type
    conn.execute(text("ALTER TABLE ingestion_runs DROP COLUMN IF EXISTS started_at_sgt"))
    conn.execute(text("ALTER TABLE ingestion_runs DROP COLUMN IF EXISTS completed_at_sgt"))

    # Add started_at_sgt as naive timestamp (stores SGT wall clock time)
    conn.execute(
        text("""
        ALTER TABLE ingestion_runs
        ADD COLUMN started_at_sgt TIMESTAMP WITHOUT TIME ZONE
    """)
    )
    print("✓ Added started_at_sgt column (Naive)")

    # Add completed_at_sgt as naive timestamp
    conn.execute(
        text("""
        ALTER TABLE ingestion_runs
        ADD COLUMN completed_at_sgt TIMESTAMP WITHOUT TIME ZONE
    """)
    )
    print("✓ Added completed_at_sgt column (Naive)")

    conn.commit()

print("=" * 80)
print("✅ Migration successful")
print("=" * 80)
# noqa: E402
