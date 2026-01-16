"""Check HDB property info data coverage for PR6 Phase 2 feasibility."""
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
print("📊 PR6 Phase 2 Data Availability Check")
print("=" * 80)

with engine.connect() as conn:
    # Check overall coverage
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_blocks,
            COUNT(year_completed) as has_year_completed,
            ROUND(COUNT(year_completed)::numeric / COUNT(*) * 100, 1) as year_pct,
            COUNT(max_floor_lvl) as has_max_floor,
            ROUND(COUNT(max_floor_lvl)::numeric / COUNT(*) * 100, 1) as floor_pct,
            COUNT(total_dwelling_units) as has_total_units,
            ROUND(COUNT(total_dwelling_units)::numeric / COUNT(*) * 100, 1) as units_pct,
            COUNT(CASE WHEN commercial = true THEN 1 END) as has_commercial,
            COUNT(CASE WHEN market_hawker = true THEN 1 END) as has_hawker,
            COUNT(CASE WHEN multistorey_carpark = true THEN 1 END) as has_carpark,
            COUNT(CASE WHEN precinct_pavilion = true THEN 1 END) as has_pavilion,
            COUNT("1room_sold") as has_unit_mix,
            ROUND(COUNT("1room_sold")::numeric / COUNT(*) * 100, 1) as unit_mix_pct
        FROM blocks
    """))
    
    row = result.fetchone()
    
    print(f"\n📈 Building Characteristics Coverage:")
    print(f"  Total blocks: {row[0]:,}")
    print(f"  Year completed: {row[1]:,} ({row[2]}%)")
    print(f"  Max floor level: {row[3]:,} ({row[4]}%)")
    print(f"  Total dwelling units: {row[5]:,} ({row[6]}%)")
    
    print(f"\n🏪 Amenity Flags Coverage:")
    print(f"  Commercial space: {row[7]:,} blocks")
    print(f"  Market/Hawker: {row[8]:,} blocks")
    print(f"  Multi-storey carpark: {row[9]:,} blocks")
    print(f"  Precinct pavilion: {row[10]:,} blocks")
    
    print(f"\n🏠 Unit Mix Data Coverage:")
    print(f"  Has unit mix data: {row[11]:,} ({row[12]}%)")
    
    # Check sample unit mix data
    print(f"\n📊 Sample Unit Mix Data (first 5 blocks with data):")
    sample = conn.execute(text("""
        SELECT 
            block, street, town,
            "1room_sold", "2room_sold", "3room_sold", "4room_sold", "5room_sold",
            exec_sold, multigen_sold, studio_apartment_sold,
            total_dwelling_units
        FROM blocks
        WHERE "1room_sold" IS NOT NULL
        LIMIT 5
    """))
    
    for row in sample:
        total_sold = sum([row[i] or 0 for i in range(3, 11)])
        print(f"  Block {row[0]} {row[1]}, {row[2]}")
        print(f"    Total units: {row[11] or 'N/A'}")
        print(f"    Sold units breakdown: 1R:{row[3] or 0}, 2R:{row[4] or 0}, 3R:{row[5] or 0}, 4R:{row[6] or 0}, 5R:{row[7] or 0}, Exec:{row[8] or 0}")
        print(f"    Total sold: {total_sold}")
        print()

print("=" * 80)
print("\n✅ PR6 Phase 2 Feasibility Assessment:")
print("  Feature 1 (Building Age): ✅ FEASIBLE if year_completed coverage > 80%")
print("  Feature 2 (Amenity Icons): ✅ FEASIBLE (amenity flags available)")
print("  Feature 3 (Unit Mix Chart): ✅ FEASIBLE if unit_mix coverage > 70%")
print("  Feature 4 (Age Adjustment): ⚠️  REQUIRES year_completed coverage > 90%")
print("=" * 80)
