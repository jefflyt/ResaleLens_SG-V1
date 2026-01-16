"""Random sampling test for postal code accuracy."""
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
from src.resalelens.utils.postal_code_patterns import generate_hdb_postal_code

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

print("=" * 80)
print("🎲 Random Postal Code Accuracy Test")
print("=" * 80)

# Sample 30 random blocks
sample_size = 30

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, block, town, postal_code
        FROM blocks 
        WHERE postal_code IS NOT NULL
        ORDER BY RANDOM()
        LIMIT :sample_size
    """), {"sample_size": sample_size})
    
    blocks = result.fetchall()
    
    print(f"\nTesting {len(blocks)} randomly sampled blocks...\n")
    print(f"{'Block':<10} {'Town':<20} {'Stored':<10} {'Expected':<30} {'Status'}")
    print("-" * 90)
    
    passed = 0
    failed = 0
    
    for block_id, block_num, town, stored_postal in blocks:
        # Generate expected postal codes
        expected = generate_hdb_postal_code(block_num, town)
        
        # Check if stored postal matches any expected value
        if stored_postal in expected:
            status = "✅ MATCH"
            passed += 1
        else:
            status = "❌ MISMATCH"
            failed += 1
        
        expected_str = str(expected) if len(str(expected)) <= 30 else str(expected)[:27] + "..."
        print(f"{block_num:<10} {town:<20} {stored_postal:<10} {expected_str:<30} {status}")
    
    print("-" * 90)
    print(f"\nResults:")
    print(f"  ✅ Passed: {passed}/{len(blocks)} ({passed/len(blocks)*100:.1f}%)")
    print(f"  ❌ Failed: {failed}/{len(blocks)}")
    
    if failed == 0:
        print(f"\n🎉 Perfect accuracy! All {passed} random blocks have correct postal codes.")
    else:
        print(f"\n⚠️  {failed} mismatches detected. These may be legacy data or special cases.")

print("=" * 80)
