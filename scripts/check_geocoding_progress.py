#!/usr/bin/env python3
"""Check block geocoding progress."""

from src.resalelens.database import SessionLocal
from src.resalelens.models import Block, IngestionRun
from datetime import datetime

db = SessionLocal()

# Check geocoding progress
total = db.query(Block).count()
geocoded = db.query(Block).filter(Block.latitude.isnot(None)).count()
remaining = total - geocoded
progress_pct = (geocoded / total * 100) if total > 0 else 0

print("=" * 60)
print("BLOCK GEOCODING PROGRESS")
print("=" * 60)
print(f"Total blocks:     {total:,}")
print(f"Geocoded:         {geocoded:,}")
print(f"Remaining:        {remaining:,}")
print(f"Progress:         {progress_pct:.1f}%")
print("=" * 60)

# Estimate time remaining (assuming ~1 second per block)
if geocoded > 0 and remaining > 0:
    avg_time_per_block = 1.5  # seconds (conservative estimate)
    est_seconds = remaining * avg_time_per_block
    est_minutes = est_seconds / 60
    est_hours = est_minutes / 60
    
    if est_hours > 1:
        print(f"Estimated time remaining: ~{est_hours:.1f} hours")
    else:
        print(f"Estimated time remaining: ~{est_minutes:.0f} minutes")
    print("=" * 60)

db.close()
