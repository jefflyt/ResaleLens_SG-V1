#!/usr/bin/env python3
"""Run VACUUM on block_pois table to reclaim disk space."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from resalelens.database import engine

def vacuum_block_pois():
    """Run VACUUM on block_pois table."""
    # Get raw connection (not in transaction)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        print("Running VACUUM FULL on block_pois table...")
        print("This may take a few minutes...")
        conn.execute(text("VACUUM FULL block_pois"))
        print("✓ VACUUM complete")
        
        # Check new size
        size_query = text("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('public.block_pois')) AS size
            FROM pg_tables 
            WHERE tablename = 'block_pois';
        """)
        new_size = conn.execute(size_query).scalar()
        print(f"✓ New table size: {new_size}")

if __name__ == "__main__":
    vacuum_block_pois()
