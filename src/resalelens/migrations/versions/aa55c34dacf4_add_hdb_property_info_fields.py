"""add_hdb_property_info_fields

Revision ID: aa55c34dacf4
Revises: 5cb8c456550e
Create Date: 2026-01-10 16:36:12.751467+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa55c34dacf4"
down_revision: str | None = "5cb8c456550e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add HDB property information fields to blocks table."""
    # Building characteristics
    op.add_column("blocks", sa.Column("max_floor_lvl", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("year_completed", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("total_dwelling_units", sa.Integer(), nullable=True))

    # Facility flags
    op.add_column(
        "blocks", sa.Column("residential", sa.Boolean(), nullable=True, server_default="true")
    )
    op.add_column(
        "blocks", sa.Column("commercial", sa.Boolean(), nullable=True, server_default="false")
    )
    op.add_column(
        "blocks", sa.Column("market_hawker", sa.Boolean(), nullable=True, server_default="false")
    )
    op.add_column(
        "blocks",
        sa.Column("multistorey_carpark", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "blocks",
        sa.Column("precinct_pavilion", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "blocks", sa.Column("miscellaneous", sa.Boolean(), nullable=True, server_default="false")
    )

    # Unit mix - sold units
    op.add_column("blocks", sa.Column("1room_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("2room_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("3room_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("4room_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("5room_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("exec_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("multigen_sold", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("studio_apartment_sold", sa.Integer(), nullable=True))

    # Unit mix - rental units
    op.add_column("blocks", sa.Column("1room_rental", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("2room_rental", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("3room_rental", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("other_room_rental", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove HDB property information fields from blocks table."""
    # Remove in reverse order
    op.drop_column("blocks", "other_room_rental")
    op.drop_column("blocks", "3room_rental")
    op.drop_column("blocks", "2room_rental")
    op.drop_column("blocks", "1room_rental")

    op.drop_column("blocks", "studio_apartment_sold")
    op.drop_column("blocks", "multigen_sold")
    op.drop_column("blocks", "exec_sold")
    op.drop_column("blocks", "5room_sold")
    op.drop_column("blocks", "4room_sold")
    op.drop_column("blocks", "3room_sold")
    op.drop_column("blocks", "2room_sold")
    op.drop_column("blocks", "1room_sold")

    op.drop_column("blocks", "miscellaneous")
    op.drop_column("blocks", "precinct_pavilion")
    op.drop_column("blocks", "multistorey_carpark")
    op.drop_column("blocks", "market_hawker")
    op.drop_column("blocks", "commercial")
    op.drop_column("blocks", "residential")

    op.drop_column("blocks", "total_dwelling_units")
    op.drop_column("blocks", "year_completed")
    op.drop_column("blocks", "max_floor_lvl")
