"""Setup SGT columns via Database Trigger.

This ensures:
1. Python code (App Logic) only deals with UTC.
2. Database automatically maintains SGT columns for readability.
"""
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
engine = create_engine(database_url)

print("=" * 80)
print("⚙️  Setting up SGT Auto-Population Trigger")
print("=" * 80)

with engine.connect() as conn:
    # 1. Ensure columns exist (Naive Timestamp)
    # We use "IF NOT EXISTS" to be safe.
    conn.execute(text("""
        ALTER TABLE ingestion_runs 
        ADD COLUMN IF NOT EXISTS started_at_sgt TIMESTAMP WITHOUT TIME ZONE
    """))
    conn.execute(text("""
        ALTER TABLE ingestion_runs 
        ADD COLUMN IF NOT EXISTS completed_at_sgt TIMESTAMP WITHOUT TIME ZONE
    """))
    print("✓ Columns verified")

    # 2. Create Trigger Function
    # This function converts the UTC columns (started_at, completed_at)
    # to Singapore Time (naive) and assigns to the _sgt columns.
    ddl_function = """
    CREATE OR REPLACE FUNCTION update_sgt_columns_func()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Convert started_at (TIMESTAMPTZ) to Singapore Time (Naive)
        IF NEW.started_at IS NOT NULL THEN
            NEW.started_at_sgt := NEW.started_at AT TIME ZONE 'Asia/Singapore';
        ELSE
            NEW.started_at_sgt := NULL;
        END IF;

        -- Convert completed_at (TIMESTAMPTZ) to Singapore Time (Naive)
        IF NEW.completed_at IS NOT NULL THEN
            NEW.completed_at_sgt := NEW.completed_at AT TIME ZONE 'Asia/Singapore';
        ELSE
            NEW.completed_at_sgt := NULL;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    conn.execute(text(ddl_function))
    print("✓ Trigger function created defined")

    # 3. Create Trigger
    # Fires BEFORE INSERT or UPDATE to set the SGT values based on the UTC values.
    conn.execute(text("DROP TRIGGER IF EXISTS set_sgt_timestamp ON ingestion_runs"))
    
    ddl_trigger = """
    CREATE TRIGGER set_sgt_timestamp
    BEFORE INSERT OR UPDATE ON ingestion_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_sgt_columns_func();
    """
    conn.execute(text(ddl_trigger))
    print("✓ Trigger 'set_sgt_timestamp' created")
    
    # 4. Backfill existing data
    conn.execute(text("""
        UPDATE ingestion_runs 
        SET started_at = started_at 
        WHERE started_at_sgt IS NULL
    """))
    print("✓ Backfill triggered (dummy update)")
    
    conn.commit()

print("=" * 80)
print("✅ Trigger setup successful. SGT columns will auto-update.")
print("=" * 80)
