#!/usr/bin/env python3
"""Script to check current ingestion status."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resalelens.database import SessionLocal
from src.resalelens.models import IngestionRun, IngestionStatus

def check_ingestion_status():
    """Check status of recent ingestion runs."""
    db = SessionLocal()
    try:
        # Get latest run for each dataset
        datasets = ["hdb_transactions", "hdb_postal_codes", "hdb_property_info", "pois", "block_pois"]
        
        print("\n" + "="*70)
        print("INGESTION STATUS SUMMARY")
        print("="*70)
        print(f"{'Dataset':<25} {'Status':<15} {'Last Run':<25}")
        print("-"*70)
        
        for dataset in datasets:
            latest_run = (
                db.query(IngestionRun)
                .filter(IngestionRun.dataset_name == dataset)
                .order_by(IngestionRun.started_at.desc())
                .first()
            )
            
            if latest_run:
                status = latest_run.status.value
                last_run = latest_run.started_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{dataset:<25} {status:<15} {last_run:<25}")
            else:
                print(f"{dataset:<25} {'NEVER RUN':<15} {'N/A':<25}")
        
        print("="*70)
        
        # Check for any IN_PROGRESS runs
        in_progress = db.query(IngestionRun).filter(
            IngestionRun.status == IngestionStatus.IN_PROGRESS
        ).count()
        
        if in_progress > 0:
            print(f"\n⚠️  WARNING: {in_progress} ingestion(s) still IN_PROGRESS")
        else:
            print(f"\n✅ No stuck ingestion runs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_ingestion_status()
