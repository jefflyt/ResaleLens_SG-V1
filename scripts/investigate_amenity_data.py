"""Investigate amenity flag data quality and coverage."""
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

env_local = Path(".env.local")
if env_local.exists():
    load_dotenv(env_local)
elif Path(".env").exists():
    load_dotenv(".env")

from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

print("=" * 80)
print("🔍 Amenity Data Investigation")
print("=" * 80)

with engine.connect() as conn:
    # Check actual values in amenity columns
    print("\n1. Checking amenity column values distribution:")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN residential IS NOT NULL THEN 1 END) as has_residential_value,
            COUNT(CASE WHEN residential = true THEN 1 END) as residential_true,
            COUNT(CASE WHEN residential = false THEN 1 END) as residential_false,
            COUNT(CASE WHEN commercial IS NOT NULL THEN 1 END) as has_commercial_value,
            COUNT(CASE WHEN commercial = true THEN 1 END) as commercial_true,
            COUNT(CASE WHEN commercial = false THEN 1 END) as commercial_false,
            COUNT(CASE WHEN market_hawker IS NOT NULL THEN 1 END) as has_hawker_value,
            COUNT(CASE WHEN market_hawker = true THEN 1 END) as hawker_true,
            COUNT(CASE WHEN market_hawker = false THEN 1 END) as hawker_false
        FROM blocks
    """))
    
    row = result.fetchone()
    print(f"\nTotal blocks: {row[0]:,}")
    print(f"\nResidential flag:")
    print(f"  Has value: {row[1]:,} ({row[1]/row[0]*100:.1f}%)")
    print(f"  True: {row[2]:,}")
    print(f"  False: {row[3]:,}")
    
    print(f"\nCommercial flag:")
    print(f"  Has value: {row[4]:,} ({row[4]/row[0]*100:.1f}%)")
    print(f"  True: {row[5]:,}")
    print(f"  False: {row[6]:,}")
    
    print(f"\nMarket/Hawker flag:")
    print(f"  Has value: {row[7]:,} ({row[7]/row[0]*100:.1f}%)")
    print(f"  True: {row[8]:,}")
    print(f"  False: {row[9]:,}")
    
    # Sample blocks with commercial=true
    print(f"\n2. Sample blocks with commercial=true:")
    sample = conn.execute(text("""
        SELECT block, street, town, commercial, market_hawker, multistorey_carpark, precinct_pavilion
        FROM blocks
        WHERE commercial = true
        LIMIT 10
    """))
    
    for row in sample:
        print(f"  {row[0]} {row[1]}, {row[2]}")
        print(f"    Commercial: {row[3]}, Hawker: {row[4]}, Carpark: {row[5]}, Pavilion: {row[6]}")
    
    # Check if ingestion has been run
    print(f"\n3. Checking ingestion history:")
    ing_result = conn.execute(text("""
        SELECT dataset_name, started_at_sgt, status, rows_processed
        FROM ingestion_runs
        WHERE dataset_name = 'hdb_property_info'
        ORDER BY started_at DESC
        LIMIT 5
    """))
    
    runs = ing_result.fetchall()
    if runs:
        print(f"  Found {len(runs)} HDB property info ingestion runs:")
        for run in runs:
            print(f"    {run[0]}: {run[1]} - {run[2]} ({run[3]} rows)")
    else:
        print(f"  ⚠️  NO HDB property info ingestion runs found!")
        print(f"  This explains the low amenity data!")

print("=" * 80)
print("\n📊 Analysis:")
print("  If amenity columns are NULL: Ingestion hasn't been run")
print("  If amenity columns are mostly FALSE: Data is accurate (most blocks are residential)")
print("=" * 80)
