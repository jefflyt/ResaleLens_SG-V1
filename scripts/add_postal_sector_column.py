"""Add postal_sector column to blocks table.

This migration adds the postal_sector column to the blocks table
and creates an index for efficient sector-based lookups.

Usage:
    python scripts/add_postal_sector_column.py
"""

from sqlalchemy import create_engine, text
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local first (priority), then .env
env_local = Path(".env.local")
env_file = Path(".env")

if env_local.exists():
    load_dotenv(env_local)
    print(f"Loaded environment from {env_local}")
elif env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from {env_file}")
else:
    print("No .env file found")

def add_postal_sector_column():
    """Add postal_sector column and index to blocks table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return

    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Add postal_sector column if not exists
        print("Adding postal_sector column...")
        conn.execute(text(
            "ALTER TABLE blocks ADD COLUMN IF NOT EXISTS postal_sector VARCHAR(2)"
        ))
        conn.commit()
        print("✓ postal_sector column added")
        
        # Create index if not exists
        print("Creating index on postal_sector...")
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_blocks_postal_sector ON blocks(postal_sector)"
        ))
        conn.commit()
        print("✓ Index idx_blocks_postal_sector created")
        
        # Create index on postal_code if not exists
        print("Creating index on postal_code...")
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_blocks_postal_code ON blocks(postal_code)"
        ))
        conn.commit()
        print("✓ Index idx_blocks_postal_code created")
        
        print("\n✅ Migration complete!")

if __name__ == "__main__":
    add_postal_sector_column()
