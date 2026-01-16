"""Transaction backfill ingestion to populate block_id, latitude, and longitude.

This module links transactions to blocks and populates geocoded coordinates
by matching on (block, street) with the blocks table.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from .utils import log_ingestion_run


def ingest_transaction_backfill(session: Session) -> dict[str, int]:
    """
    Backfill block_id, latitude, and longitude for transactions.

    Links transactions to blocks by matching on (block, street) and
    populates latitude/longitude from the blocks table.

    Args:
        session: SQLAlchemy session

    Returns:
        Dictionary with backfill summary:
        - total_transactions: Total transactions in database
        - matched: Number of transactions successfully matched to blocks
        - unmatched: Number of transactions without matching blocks
        - match_rate: Percentage of transactions matched (0-100)

    Raises:
        Exception: If backfill fails critically
    """
    summary = {
        "total_transactions": 0,
        "matched": 0,
        "unmatched": 0,
        "match_rate": 0.0,
    }

    with log_ingestion_run(session, "transaction_backfill") as run:
        print("Starting transaction backfill...")

        # Check current state
        total = session.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        unmatched_before = session.execute(
            text("SELECT COUNT(*) FROM transactions WHERE block_id IS NULL")
        ).scalar()

        summary["total_transactions"] = total or 0
        print(f"Total transactions: {summary['total_transactions']:,}")
        print(f"Transactions without block_id: {unmatched_before:,}")

        # Backfill using SQL UPDATE with JOIN
        # Populates block_id, latitude, and longitude from blocks table
        print("\nRunning backfill UPDATE query...")
        backfill_sql = """
            UPDATE transactions t
            SET 
                block_id = b.id,
                latitude = b.latitude,
                longitude = b.longitude
            FROM blocks b
            WHERE t.block = b.block 
            AND t.street = b.street
            AND t.block_id IS NULL
        """

        session.execute(text(backfill_sql))
        session.commit()

        print("✅ Backfill complete")

        # Check final state
        unmatched_after = session.execute(
            text("SELECT COUNT(*) FROM transactions WHERE block_id IS NULL")
        ).scalar()
        matched = (total or 0) - (unmatched_after or 0)

        summary["matched"] = matched
        summary["unmatched"] = unmatched_after or 0
        summary["match_rate"] = (
            (matched / summary["total_transactions"] * 100)
            if summary["total_transactions"] > 0
            else 0.0
        )

        print("\n📊 Results:")
        print(f"   Total transactions: {summary['total_transactions']:,}")
        print(f"   Matched (with block_id): {summary['matched']:,}")
        print(f"   Unmatched (block_id IS NULL): {summary['unmatched']:,}")
        print(f"   Match rate: {summary['match_rate']:.2f}%")

        if summary["unmatched"] > 0:
            print(f"\n⚠️  WARNING: {summary['unmatched']} transactions could not be matched!")
            print("Sample unmatched (block, street) combinations:")

            samples = session.execute(
                text(
                    """
                    SELECT DISTINCT block, street
                    FROM transactions
                    WHERE block_id IS NULL
                    LIMIT 10
                """
                )
            ).fetchall()

            for block, street in samples:
                print(f"  - {block} {street}")
        else:
            print("\n✅ All transactions successfully matched to blocks!")

        # Update ingestion run summary
        run.rows_processed = summary["matched"]

        print(f"Transaction backfill complete: {summary}")

    return summary
