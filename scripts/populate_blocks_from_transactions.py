"""Script to populate blocks table from existing transactions.

This script extracts unique (block, street, town) combinations from the transactions
table and creates corresponding block records. This is a prerequisite for adding
the block_id foreign key to transactions.
"""

from resalelens.database import SessionLocal
from resalelens.models import Block, Transaction


def populate_blocks_from_transactions():
    """Extract unique blocks from transactions and create block records."""
    db = SessionLocal()

    try:
        # Get unique (block, street, town) combinations from transactions
        unique_blocks = (
            db.query(
                Transaction.block,
                Transaction.street,
                Transaction.town,
            )
            .distinct()
            .all()
        )

        print(f"Found {len(unique_blocks)} unique blocks in transactions")

        # Create block records
        blocks_created = 0
        blocks_existing = 0

        for block_num, street, town in unique_blocks:
            # Check if block already exists
            existing_block = (
                db.query(Block).filter(Block.block == block_num, Block.street == street).first()
            )

            if existing_block:
                blocks_existing += 1
                continue

            # Create new block
            new_block = Block(
                block=block_num,
                street=street,
                town=town,
            )
            db.add(new_block)
            blocks_created += 1

            # Commit in batches of 100
            if blocks_created % 100 == 0:
                db.commit()
                print(f"Created {blocks_created} blocks...")

        # Final commit
        db.commit()

        print("\n✅ Blocks population complete:")
        print(f"   - Created: {blocks_created}")
        print(f"   - Already existed: {blocks_existing}")
        print(f"   - Total unique blocks: {len(unique_blocks)}")

        return blocks_created

    except Exception as e:
        db.rollback()
        print(f"❌ Error populating blocks: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_blocks_from_transactions()
