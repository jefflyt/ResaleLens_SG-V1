#!/usr/bin/env python3
"""Verify HDB property information columns in blocks table."""

import os
import sys

# Load environment from .env.local
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv('.env.local')

def check_blocks_schema():
    """Check if HDB property info columns exist in blocks table."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set")
        print("Make sure .env.local is loaded")
        return False

    print("Connecting to database...")
    engine = create_engine(db_url)
    inspector = inspect(engine)

    # Get all columns in blocks table
    try:
        columns = inspector.get_columns('blocks')
        column_names = [col['name'] for col in columns]

        print(f"\n✅ Connected! Found {len(column_names)} columns in blocks table\n")

        # Check for HDB property information fields
        expected_fields = {
            'Building Characteristics': ['max_floor_lvl', 'year_completed', 'total_dwelling_units'],
            'Facility Flags': ['residential', 'commercial', 'market_hawker', 'multistorey_carpark', 'precinct_pavilion', 'miscellaneous'],
            'Unit Mix (Sold)': ['1room_sold', '2room_sold', '3room_sold', '4room_sold', '5room_sold', 'exec_sold', 'multigen_sold', 'studio_apartment_sold'],
            'Unit Mix (Rental)': ['1room_rental', '2room_rental', '3room_rental', 'other_room_rental'],
        }

        all_exist = True
        missing_fields = []

        for category, fields in expected_fields.items():
            print(f"📋 {category}:")
            for field in fields:
                exists = field in column_names
                status = "✅" if exists else "❌"
                print(f"  {status} {field}")
                if not exists:
                    all_exist = False
                    missing_fields.append(field)
            print()

        # Summary
        print("=" * 60)
        if all_exist:
            print("✅ SUCCESS: All 27 HDB property fields exist!")
            print("\nYou can proceed with the property info ingestion.")
        else:
            print(f"❌ MISSING: {len(missing_fields)} fields are missing:")
            for field in missing_fields:
                print(f"   - {field}")
            print("\nYou need to add these columns before running ingestion.")
        print("=" * 60)

        return all_exist

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = check_blocks_schema()
    sys.exit(0 if success else 1)
