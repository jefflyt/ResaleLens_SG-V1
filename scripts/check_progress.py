"""Quick script to check ingestion progress."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(".env.local")

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Count transactions
    result = conn.execute(text("SELECT COUNT(*) as count FROM transactions"))
    count = result.scalar()
    print(f"Total transactions: {count:,}")

    # Check date range
    result = conn.execute(text("""
        SELECT
            MIN(date) as earliest,
            MAX(date) as latest,
            COUNT(DISTINCT date) as unique_dates
        FROM transactions
    """))
    row = result.fetchone()
    print(f"Date range: {row[0]} to {row[1]}")
    print(f"Unique dates: {row[2]}")

    # Check ingestion runs
    result = conn.execute(text("""
        SELECT
            id,
            dataset_name,
            status,
            rows_processed,
            started_at
        FROM ingestion_runs
        ORDER BY started_at DESC
        LIMIT 3
    """))
    print("\nRecent ingestion runs:")
    for row in result:
        print(f"  ID {row[0]}: {row[1]} - {row[2]} - {row[3]:,} rows at {row[4]}")
