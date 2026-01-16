"""Verify SGT columns in ingestion_runs."""
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load env
env_local = Path(".env.local")
if env_local.exists():
    load_dotenv(env_local)
elif Path(".env").exists():
    load_dotenv(".env")

from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

print("=" * 80)
print("🔍 Checking SGT Columns in ingestion_runs")
print("=" * 80)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, dataset_name, started_at_sgt, completed_at_sgt
        FROM ingestion_runs
        ORDER BY started_at DESC
        LIMIT 1
    """))
    
    row = result.fetchone()
    if row:
        print(f"Latest Run ID: {row[0]}")
        print(f"Dataset: {row[1]}")
        print(f"Started (SGT): {row[2]}")
        print(f"Completed (SGT): {row[3]}")
        
        if row[2] and row[3]:
            print("✅ SGT columns populated!")
            # Basic sanity check (should be ~8 hours ahead of UTC if checking offset, 
            # but seeing '+08' in print output is enough)
        else:
            print("❌ SGT columns are NULL")
    else:
        print("❌ No runs found.")

print("=" * 80)
