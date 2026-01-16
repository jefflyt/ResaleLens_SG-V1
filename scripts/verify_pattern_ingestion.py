"""Verify specific blocks have correctly encoded postal codes after pattern ingestion."""

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
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

engine = create_engine(database_url)

print("=" * 80)
print("🔍 Verifying Postal Code Pattern Logic in Database")
print("=" * 80)

test_blocks = [
    # Block, Town, Expected Pattern
    ("123", "BEDOK", ["460123", "470123", "480123"]),
    ("471C", "SENGKANG", ["543471", "823471"]),
    # 128B BEDOK Removed (Does not exist in DB)
    ("310A", "PUNGGOL", ["821310"]),
    ("310B", "PUNGGOL", ["822310"]),
    ("506B", "YISHUN", ["762506"]), # Replaced '5' with '506B'
    ("238", "TAMPINES", ["520238"]),
]

with engine.connect() as conn:
    print(f"{'Block':<8} {'Town':<15} {'Found Postal':<15} {'Expected (Any)':<30} {'Status'}")
    print("-" * 90)
    
    passed = 0
    total = 0
    
    for block, town, expected in test_blocks:
        result = conn.execute(text("""
            SELECT postal_code 
            FROM blocks 
            WHERE block = :block AND town = :town
        """), {"block": block, "town": town})
        
        row = result.fetchone()
        found_postal = row[0] if row else "NOT FOUND"
        
        match = False
        if found_postal != "NOT FOUND":
            if found_postal in expected:
                match = True
        
        # Checking logic might be tricky if town mappings are slightly different in DB
        # But let's see what we find.
        
        status = "✅ PASS" if match else "❌ FAIL"
        if match: passed += 1
        total += 1
        
        print(f"{block:<8} {town:<15} {str(found_postal):<15} {str(expected):<30} {status}")

    print("-" * 90)
    print(f"Verification Results: {passed}/{total} Passed")
    print("=" * 80)
