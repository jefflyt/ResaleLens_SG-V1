"""Run ingestion for blocks with missing postal codes only."""
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

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.resalelens.ingestion.hdb_postal_codes import ingest_hdb_postal_codes

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

print("=" * 80)
print("🚀 Running Incremental Ingestion (Filling Missing Postal Codes)")
print("=" * 80)

with Session(engine) as session:
    # skip_existing=True is default, so it targets missing ones
    summary = ingest_hdb_postal_codes(session, skip_existing=True)
    
    print("\nSummary:")
    for k, v in summary.items():
        print(f"{k}: {v}")

print("=" * 80)
