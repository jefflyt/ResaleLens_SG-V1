#!/usr/bin/env python3
"""Clean up block_pois table by removing distances > 1000m."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from resalelens.database import SessionLocal

def cleanup_block_pois(max_distance_m: int = 1000):
    """Remove block-POI distances above threshold."""
    db = SessionLocal()
    
    try:
        # Get current count
        current_count = db.execute(text("SELECT COUNT(*) FROM block_pois")).scalar()
        print(f"Current block_pois records: {current_count:,}")
        
        # Count records to delete
        delete_count_query = text(f"""
            SELECT COUNT(*) 
            FROM block_pois 
            WHERE distance_m > {max_distance_m}
        """)
        delete_count = db.execute(delete_count_query).scalar()
        print(f"Records to delete (> {max_distance_m}m): {delete_count:,}")
        
        # Ask for confirmation
        response = input(f"\nThis will delete {delete_count:,} records. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        # Delete records
        print(f"\nDeleting records > {max_distance_m}m...")
        delete_query = text(f"""
            DELETE FROM block_pois 
            WHERE distance_m > {max_distance_m}
        """)
        db.execute(delete_query)
        db.commit()
        
        # Get new count
        new_count = db.execute(text("SELECT COUNT(*) FROM block_pois")).scalar()
        print(f"✓ Deleted {delete_count:,} records")
        print(f"✓ Remaining records: {new_count:,}")
        
        # VACUUM to reclaim space
        print("\nRunning VACUUM to reclaim disk space...")
        print("(This may take a few minutes...)")
        db.execute(text("VACUUM FULL block_pois"))
        print("✓ VACUUM complete")
        
        # Check new size
        size_query = text("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('public.block_pois')) AS size
            FROM pg_tables 
            WHERE tablename = 'block_pois';
        """)
        new_size = db.execute(size_query).scalar()
        print(f"\n✓ New table size: {new_size}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    # Allow custom threshold via command line
    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    cleanup_block_pois(threshold)
