"""Clean test database to remove old test data."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load test environment
load_dotenv(".env.local")

# Use testing database
database_url = os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL must be set")

engine = create_engine(database_url)

# Tables to clean (in dependency order - children first)
tables_to_clean = [
    "block_pois",
    "transactions",
    "pois",
    "leads",
    "ingestion_runs",
    "blocks",
    "users",
]

print("Cleaning test database...")
with engine.connect() as conn:
    with conn.begin():
        for table in tables_to_clean:
            result = conn.execute(text(f"DELETE FROM {table}"))
            print(f"Deleted {result.rowcount} rows from {table}")

print("Database cleaned successfully!")
