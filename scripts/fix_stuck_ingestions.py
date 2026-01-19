#!/usr/bin/env python3
"""Script to fix stuck ingestion runs in the database."""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resalelens.database import SessionLocal
from src.resalelens.models import IngestionRun, IngestionStatus

def fix_stuck_ingestions():
    """Mark all IN_PROGRESS ingestion runs as FAILED."""
    db = SessionLocal()
    try:
        # Find all stuck ingestion runs
        stuck_runs = db.query(IngestionRun).filter(
            IngestionRun.status == IngestionStatus.IN_PROGRESS
        ).all()
        
        if not stuck_runs:
            print("✅ No stuck ingestion runs found.")
            return
        
        print(f"Found {len(stuck_runs)} stuck ingestion run(s):")
        for run in stuck_runs:
            print(f"  - {run.dataset_name} (started: {run.started_at})")
        
        # Mark them as failed
        for run in stuck_runs:
            run.status = IngestionStatus.FAILED
            run.completed_at = datetime.now(timezone.utc)
            run.error_summary = "Ingestion interrupted (process killed)"
        
        db.commit()
        print(f"\n✅ Marked {len(stuck_runs)} ingestion run(s) as FAILED.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_stuck_ingestions()
