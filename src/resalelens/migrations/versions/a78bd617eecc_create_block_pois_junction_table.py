"""create_block_pois_junction_table

Revision ID: a78bd617eecc
Revises: 7eb00197f47f
Create Date: 2026-01-11 12:47:23.049043+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "a78bd617eecc"
down_revision: str | None = "7eb00197f47f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create block_pois junction table and populate with distances."""
    connection = op.get_bind()

    print("Creating block_pois junction table...")

    # Create block_pois table
    op.create_table(
        "block_pois",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.Integer(), nullable=False),
        sa.Column("poi_id", sa.Integer(), nullable=False),
        sa.Column("distance_m", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], name="fk_block_pois_block_id"),
        sa.ForeignKeyConstraint(["poi_id"], ["pois.id"], name="fk_block_pois_poi_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("block_id", "poi_id", name="uq_block_poi"),
        sa.CheckConstraint("distance_m >= 0", name="check_distance_positive"),
    )

    # Create indexes
    op.create_index("ix_block_pois_block_id_distance", "block_pois", ["block_id", "distance_m"])
    op.create_index("ix_block_pois_poi_id", "block_pois", ["poi_id"])

    print("✅ Table and indexes created")

    # Populate distances using Haversine formula
    print("Calculating and populating block-POI distances...")
    print("This may take a few minutes for ~45k distance calculations...")

    # SQL to calculate distances using Haversine formula
    # Only calculate for distances <= 2000m (2km)
    populate_sql = """
    INSERT INTO block_pois (block_id, poi_id, distance_m, created_at)
    SELECT
        block_id,
        poi_id,
        distance_m,
        NOW() AS created_at
    FROM (
        SELECT
            b.id AS block_id,
            p.id AS poi_id,
            -- Haversine formula for distance in meters
            (
                6371000 * 2 * ASIN(
                    SQRT(
                        POWER(SIN(RADIANS(p.latitude - b.latitude) / 2), 2) +
                        COS(RADIANS(b.latitude)) * COS(RADIANS(p.latitude)) *
                        POWER(SIN(RADIANS(p.longitude - b.longitude) / 2), 2)
                    )
                )
            ) AS distance_m
        FROM blocks b
        CROSS JOIN pois p
        WHERE
            b.latitude IS NOT NULL
            AND b.longitude IS NOT NULL
            AND (
                -- Quick bounding box filter (approx 2km = 0.018 degrees)
                ABS(b.latitude - p.latitude) <= 0.018
                AND ABS(b.longitude - p.longitude) <= 0.018
            )
    ) AS distances
    WHERE distance_m <= 2000  -- Only store distances within 2km
    ORDER BY block_id, distance_m;
    """

    result = connection.execute(text(populate_sql))
    row_count = result.rowcount if hasattr(result, "rowcount") else 0

    print(f"✅ Populated {row_count:,} block-POI distance records")
    print("✅ Block-POI junction table migration complete!")


def downgrade() -> None:
    """Drop block_pois table."""
    print("Dropping block_pois junction table...")

    # Drop indexes
    op.drop_index("ix_block_pois_poi_id", table_name="block_pois")
    op.drop_index("ix_block_pois_block_id_distance", table_name="block_pois")

    # Drop table
    op.drop_table("block_pois")

    print("✅ Block-POI junction table dropped")
