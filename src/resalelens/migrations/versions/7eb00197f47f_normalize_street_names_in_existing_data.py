"""normalize_street_names_in_existing_data

Revision ID: 7eb00197f47f
Revises: 48e304bbcece
Create Date: 2026-01-11 07:57:36.131160+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7eb00197f47f'
down_revision: str | None = '48e304bbcece'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Normalize street names in transactions and blocks tables."""
    connection = op.get_bind()

    print("Normalizing street names in existing data...")
    print("This will expand abbreviations: ST→STREET, AVE→AVENUE, etc.")

    # Define abbreviation replacements (same as normalize_street_name function)
    abbreviations = [
        (" ST ", " STREET "),
        (" AVE ", " AVENUE "),
        (" DR ", " DRIVE "),
        (" RD ", " ROAD "),
        (" CRES ", " CRESCENT "),
        (" PL ", " PLACE "),
        (" TER ", " TERRACE "),
        (" CL ", " CLOSE "),
        (" CTRL ", " CENTRAL "),
        (" PK ", " PARK "),
        (" HTS ", " HEIGHTS "),
        (" GDN ", " GARDEN "),
        (" GDNS ", " GARDENS "),
        (" LOR ", " LORONG "),
        (" JLN ", " JALAN "),
        (" UPP ", " UPPER "),
        (" LWR ", " LOWER "),
        (" NTH ", " NORTH "),
        (" STH ", " SOUTH "),
    ]

    # Build SQL for transactions table
    # Start with adding spaces at boundaries
    transactions_sql = "UPDATE transactions SET street = TRIM(street_normalized) FROM ("
    transactions_sql += "  SELECT id, "

    # Chain REPLACE functions
    replace_chain = "' ' || UPPER(TRIM(street)) || ' '"
    for abbr, full in abbreviations:
        replace_chain = f"REPLACE({replace_chain}, '{abbr}', '{full}')"

    transactions_sql += f"    {replace_chain} AS street_normalized"
    transactions_sql += "  FROM transactions"
    transactions_sql += ") AS normalized WHERE transactions.id = normalized.id"

    print("Normalizing transactions table...")
    result = connection.execute(sa.text(transactions_sql))
    print(f"✅ Updated {result.rowcount if hasattr(result, 'rowcount') else 'all'} transaction records")

    # Build SQL for blocks table
    blocks_sql = "UPDATE blocks SET street = TRIM(street_normalized) FROM ("
    blocks_sql += "  SELECT id, "

    # Chain REPLACE functions (same as above)
    replace_chain = "' ' || UPPER(TRIM(street)) || ' '"
    for abbr, full in abbreviations:
        replace_chain = f"REPLACE({replace_chain}, '{abbr}', '{full}')"

    blocks_sql += f"    {replace_chain} AS street_normalized"
    blocks_sql += "  FROM blocks"
    blocks_sql += ") AS normalized WHERE blocks.id = normalized.id"

    print("Normalizing blocks table...")
    result = connection.execute(sa.text(blocks_sql))
    print(f"✅ Updated {result.rowcount if hasattr(result, 'rowcount') else 'all'} block records")

    print("✅ Street name normalization complete!")


def downgrade() -> None:
    """Downgrade: Cannot reverse normalization without original data."""
    print("⚠️  WARNING: Cannot reverse street name normalization.")
    print("Original abbreviated data is lost. This is a one-way migration.")
    print("If you need to restore original data, you must re-ingest from source.")
    pass
