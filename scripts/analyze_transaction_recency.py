"""Analyze transaction recency for blocks with vs without postal codes."""

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
print("📅 Transaction Recency Analysis: Blocks With vs Without Postal Codes")
print("=" * 80)

with engine.connect() as conn:
    # Latest transaction date for blocks WITH postal codes
    print("\n✅ BLOCKS WITH POSTAL CODES:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT b.id) as block_count,
            MIN(t.date) as first_transaction,
            MAX(t.date) as latest_transaction,
            COUNT(t.id) as total_transactions
        FROM blocks b
        JOIN transactions t ON b.id = t.block_id
        WHERE b.postal_code IS NOT NULL
    """))
    row = result.fetchone()
    print(f"Blocks with postal codes:  {row[0]:,}")
    print(f"Total transactions:        {row[3]:,}")
    print(f"First transaction:         {row[1]}")
    print(f"Latest transaction:        {row[2]}")
    
    # Latest transaction date for blocks WITHOUT postal codes
    print("\n❌ BLOCKS WITHOUT POSTAL CODES:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT b.id) as block_count,
            MIN(t.date) as first_transaction,
            MAX(t.date) as latest_transaction,
            COUNT(t.id) as total_transactions
        FROM blocks b
        JOIN transactions t ON b.id = t.block_id
        WHERE b.postal_code IS NULL
    """))
    row = result.fetchone()
    print(f"Blocks without postal:     {row[0]:,}")
    print(f"Total transactions:        {row[3]:,}")
    print(f"First transaction:         {row[1]}")
    print(f"Latest transaction:        {row[2]}")
    
    # Transaction distribution by year
    print("\n📊 TRANSACTION COUNT BY YEAR (blocks without postal codes):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            EXTRACT(YEAR FROM t.date) as year,
            COUNT(*) as transaction_count
        FROM blocks b
        JOIN transactions t ON b.id = t.block_id
        WHERE b.postal_code IS NULL
        GROUP BY EXTRACT(YEAR FROM t.date)
        ORDER BY year DESC
        LIMIT 10
    """))
    
    print(f"{'Year':<10} {'Transactions':>15}")
    print("-" * 80)
    for row in result:
        print(f"{int(row[0]):<10} {row[1]:>15,}")
    
    # Most recent transactions for unmatched blocks
    print("\n🔍 RECENT TRANSACTIONS (blocks without postal codes):")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            b.block,
            b.street,
            b.town,
            MAX(t.date) as latest_transaction,
            COUNT(t.id) as transaction_count
        FROM blocks b
        JOIN transactions t ON b.id = t.block_id
        WHERE b.postal_code IS NULL
        GROUP BY b.id, b.block, b.street, b.town
        ORDER BY latest_transaction DESC
        LIMIT 15
    """))
    
    print(f"{'Block':<8} {'Street':<30} {'Town':<15} {'Latest':<12} {'Count':>6}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]:<8} {row[1][:29]:<30} {row[2]:<15} {str(row[3])[:10]:<12} {row[4]:>6}")

print("\n" + "=" * 80)
