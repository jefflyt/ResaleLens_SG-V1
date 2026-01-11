"""Backfill block_id for existing transactions.

This script populates the block_id foreign key for all transactions
by matching on (block, street) with the blocks table.
"""

from sqlalchemy import text

from resalelens.database import SessionLocal


def backfill_transaction_block_ids():
    """Backfill block_id for all transactions."""
    db = SessionLocal()

    try:
        print("Starting backfill of transaction block_ids...")

        # Check current state
        total = db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
        unmatched_before = db.execute(
            text("SELECT COUNT(*) FROM transactions WHERE block_id IS NULL")
        ).scalar()

        print(f"Total transactions: {total:,}")
        print(f"Transactions without block_id: {unmatched_before:,}")

        # Backfill using SQL UPDATE with JOIN
        print("\nRunning backfill UPDATE query...")
        backfill_sql = """
            UPDATE transactions t
            SET block_id = b.id
            FROM blocks b
            WHERE t.block = b.block AND t.street = b.street
            AND t.block_id IS NULL
        """

        result = db.execute(text(backfill_sql))
        db.commit()

        print("✅ Backfill complete")

        # Check final state
        unmatched_after = db.execute(
            text("SELECT COUNT(*) FROM transactions WHERE block_id IS NULL")
        ).scalar()
        matched = total - unmatched_after

        print("\n📊 Results:")
        print(f"   Total transactions: {total:,}")
        print(f"   Matched (with block_id): {matched:,}")
        print(f"   Unmatched (block_id IS NULL): {unmatched_after:,}")
        print(f"   Match rate: {(matched/total*100):.2f}%")

        if unmatched_after > 0:
            print(f"\n⚠️  WARNING: {unmatched_after} transactions could not be matched!")
            print("Sample unmatched (block, street) combinations:")

            samples = db.execute(
                text("""
                    SELECT DISTINCT block, street 
                    FROM transactions 
                    WHERE block_id IS NULL 
                    LIMIT 10
                """)
            ).fetchall()

            for block, street in samples:
                print(f"  - {block} {street}")
        else:
            print("\n✅ All transactions successfully matched to blocks!")

        return {
            "total": total,
            "matched": matched,
            "unmatched": unmatched_after,
            "match_rate": (matched/total*100) if total > 0 else 0
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error during backfill: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_transaction_block_ids()
