"""Verify block_pois table data."""

import os
import sys

# Allow imports from src
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from src.resalelens.config import settings
from src.resalelens.models import POI, Block, BlockPOI


def verify_block_pois():
    # settings = get_settings() # Removed
    print(f"Connecting to DB: {settings.database_url}")
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Check totals
        total_relations = session.execute(select(func.count(BlockPOI.id))).scalar()
        print(f"Total entries in block_pois table: {total_relations}")

        if total_relations == 0:
            print("WARNING: block_pois table is empty.")

            # Check if we have source data
            total_blocks = session.execute(select(func.count(Block.id))).scalar()
            total_pois = session.execute(select(func.count(POI.id))).scalar()
            print(f"debug info: Blocks: {total_blocks}, POIs: {total_pois}")
            return

        # Check sample statistics
        avg_distance = session.execute(select(func.avg(BlockPOI.distance_m))).scalar()
        min_distance = session.execute(select(func.min(BlockPOI.distance_m))).scalar()
        max_distance = session.execute(select(func.max(BlockPOI.distance_m))).scalar()

        print("Distance stats (meters):")
        print(f"  Min: {min_distance}")
        print(f"  Max: {max_distance}")
        print(f"  Avg: {avg_distance:.2f}")

        # Check sample join
        stmt = (
            select(Block.block, Block.street, POI.name, POI.poi_type, BlockPOI.distance_m)
            .join(BlockPOI.block)
            .join(BlockPOI.poi)
            .order_by(BlockPOI.distance_m.asc())
            .limit(5)
        )
        results = session.execute(stmt).all()

        print("\nTop 5 Closest Block-POI pairs:")
        for block, street, poi_name, poi_type, dist in results:
            print(f"  {block} {street} <--> {poi_name} ({poi_type.value}): {dist:.1f}m")

        # --- Deep Verification ---
        print("\n--- Deep Verification ---")

        # 1. Blocks with NO POIs
        # Count all blocks
        total_blocks = session.execute(select(func.count(Block.id))).scalar()
        # Count blocks with at least one POI entry
        blocks_with_pois_count = session.execute(
            select(func.count(func.distinct(BlockPOI.block_id)))
        ).scalar()

        orphaned_blocks = total_blocks - blocks_with_pois_count
        print(f"Blocks coverage: {blocks_with_pois_count}/{total_blocks} ({blocks_with_pois_count/total_blocks*100:.1f}%)")
        print(f"Orphaned blocks (0 POIs within 2km): {orphaned_blocks}")

        # 2. POI Distribution per Block
        # Avg/Min/Max POIs per block
        # We can do this with a subquery or just simple math on averages
        avg_pois = total_relations / blocks_with_pois_count if blocks_with_pois_count else 0
        print(f"Avg POIs per covered block: {avg_pois:.1f}")

        # 3. POI Type Breakdown
        print("\nPOI Type Distribution (Linked):")
        poi_type_counts = session.execute(
            select(POI.poi_type, func.count(BlockPOI.id))
            .join(BlockPOI.poi)
            .group_by(POI.poi_type)
            .order_by(func.count(BlockPOI.id).desc())
        ).all()

        for p_type, count in poi_type_counts:
            print(f"  {p_type.value}: {count} links")

        # Check for missing types
        all_poi_types = session.execute(select(POI.poi_type).distinct()).scalars().all()
        linked_types = [t[0] for t in poi_type_counts]
        missing_types = set(all_poi_types) - set(linked_types)

        if missing_types:
            print(f"\nWARNING: The following POI types exist but have NO links to any block: {missing_types}")
        else:
            print("\nAll existing POI types have at least one link.")

        # 4. Investigate Orphans
        print("\n--- Orphan Analysis ---")

        # Check for missing coordinates globally (Fast check)
        missing_coords_count = session.execute(
            select(func.count(Block.id))
            .where((Block.latitude is None) | (Block.longitude is None))
        ).scalar()

        print(f"Total Blocks with MISSING coordinates: {missing_coords_count}")

        if orphaned_blocks > 0:
            print(f"Total Orphans: {orphaned_blocks}")

            if missing_coords_count == 0:
                print("All orphans have coordinates. Analyzing town distribution...")

                # Fetch all blocks
                all_blocks = session.execute(
                    select(Block.id, Block.town, Block.block, Block.street)
                ).all()

                # Fetch all covered block IDs
                covered_ids = set(session.execute(
                    select(func.distinct(BlockPOI.block_id))
                ).scalars().all())

                # Identify orphans
                orphan_towns = {}
                sample_orphans = []

                for b in all_blocks:
                    if b.id not in covered_ids:
                        # Count by town
                        orphan_towns[b.town] = orphan_towns.get(b.town, 0) + 1
                        if len(sample_orphans) < 5:
                            sample_orphans.append(f"{b.block} {b.street} ({b.town})")

                # Print stats
                print("\nOrphan Count by Town:")
                sorted_towns = sorted(orphan_towns.items(), key=lambda x: x[1], reverse=True)
                for town, count in sorted_towns[:10]:
                    print(f"  {town}: {count}")

                print("\nSample Orphans:")
                for s in sample_orphans:
                    print(f"  {s}")

        # 5. POI Data Sufficiency Check
        print("\n--- POI Data Sufficiency ---")
        poi_counts = session.execute(
            select(POI.poi_type, func.count(POI.id))
            .group_by(POI.poi_type)
            .order_by(func.count(POI.id).desc())
        ).all()

        print("Total POIs in Database:")
        for p_type, count in poi_counts:
            print(f"  {p_type.value}: {count}")





    finally:
        session.close()

if __name__ == "__main__":
    verify_block_pois()
