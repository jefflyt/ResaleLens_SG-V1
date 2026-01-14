"""Run Block-POI distance calculation."""

import os
import sys

# Allow imports from src
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.resalelens.config import settings
from src.resalelens.ingestion.block_pois import ingest_block_pois


def main():
    print("Starting Block-POI Distance Calculation...")
    print(f"Database: {settings.database_url}")

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        summary = ingest_block_pois(session)
        print("\n=== Distance Calculation Complete ===")
        print(f"Summary: {summary}")
    except Exception as e:
        print(f"\n!!! Error during ingestion: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
