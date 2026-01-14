"""
Guardrails for safe ingestion operations.

Provides safety checks to prevent accidental data loss or corruption.
"""

import os
from collections.abc import Callable
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from resalelens.models import Block, IngestionRun, Transaction


class IngestionGuardrails:
    """Safety guardrails for ingestion operations."""

    @staticmethod
    def check_database_state(db: Session) -> dict[str, int]:
        """
        Check current database state before ingestion.

        Returns:
            Dictionary with current counts of transactions, blocks, and runs
        """
        return {
            "transactions": db.query(func.count(Transaction.id)).scalar() or 0,
            "blocks": db.query(func.count(Block.id)).scalar() or 0,
            "ingestion_runs": db.query(func.count(IngestionRun.id)).scalar() or 0,
        }

    @staticmethod
    def warn_production_ingestion() -> bool:
        """
        Warn if running ingestion against production database.

        Returns:
            True if user confirms, False to abort
        """
        database_url = os.getenv("DATABASE_URL", "sqlite:///data/resalelens.db")

        if database_url.startswith("postgresql"):
            print("\n⚠️  WARNING: Running ingestion against PostgreSQL/Supabase!")
            print("   This will modify your production database.")
            print(f"   Database: {database_url.split('@')[1] if '@' in database_url else 'remote'}")

            response = input("\n   Continue? (yes/no): ").strip().lower()
            return response in ["yes", "y"]

        return True

    @staticmethod
    def validate_environment() -> tuple[bool, list[str]]:
        """
        Validate required environment variables are set.

        Returns:
            Tuple of (is_valid, list of missing variables)
        """
        required = [
            "DATA_GOV_SG_RESOURCE_ID",
            "ONEMAP_EMAIL",
            "ONEMAP_PASSWORD",
        ]

        missing = [var for var in required if not os.getenv(var)]

        return len(missing) == 0, missing

    @staticmethod
    def safe_ingestion_wrapper(
        db: Session,
        dataset: Literal["hdb_transactions", "hdb_blocks"],
        ingestion_func: "Callable[[Session], dict[str, int]]",
    ) -> dict[str, int | str]:
        """
        Wrap ingestion function with safety checks.

        Args:
            db: Database session
            dataset: Dataset name
            ingestion_func: Function to run ingestion

        Returns:
            Ingestion summary or error dict
        """
        # Check environment
        is_valid, missing = IngestionGuardrails.validate_environment()
        if not is_valid:
            return {
                "status": "error",
                "message": f"Missing environment variables: {', '.join(missing)}",
            }

        # Warn on production
        if not IngestionGuardrails.warn_production_ingestion():
            return {"status": "aborted", "message": "User cancelled ingestion"}

        # Log state before
        state_before = IngestionGuardrails.check_database_state(db)
        print("\n📊 Database state before ingestion:")
        print(f"   Transactions: {state_before['transactions']:,}")
        print(f"   Blocks: {state_before['blocks']:,}")
        print(f"   Ingestion runs: {state_before['ingestion_runs']:,}")

        # Run ingestion
        print(f"\n🚀 Starting {dataset} ingestion...\n")
        result: dict[str, int] = ingestion_func(db)

        # Log state after
        state_after = IngestionGuardrails.check_database_state(db)
        print("\n📊 Database state after ingestion:")
        print(
            f"   Transactions: {state_after['transactions']:,} (+{state_after['transactions'] - state_before['transactions']:,})"
        )
        print(
            f"   Blocks: {state_after['blocks']:,} (+{state_after['blocks'] - state_before['blocks']:,})"
        )
        print(
            f"   Ingestion runs: {state_after['ingestion_runs']:,} (+{state_after['ingestion_runs'] - state_before['ingestion_runs']:,})"
        )

        # Return with proper typing
        return dict(result)  # type: ignore[return-value]
