"""Block POI distance ingestion."""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.repositories import BlockPOIRepository
from ..models import POI, Block
from .utils import log_ingestion_run


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in meters
    """
    R = 6371000  # Radius of Earth in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def ingest_block_pois(
    session: Session, max_distance_m: float = 2000.0, batch_size: int = 100
) -> dict[str, int]:
    """
    Calculate and store distances between blocks and POIs.

    This function performs a spatial join between blocks and POIs using a
    bounding box optimization to reduce the number of distance calculations.

    Args:
        session: Database session
        max_distance_m: Maximum distance to consider (default: 2km)
        batch_size: Number of blocks to process before committing

    Returns:
        Summary of ingestion statistics
    """
    summary = {
        "blocks_processed": 0,
        "distances_calculated": 0,
        "records_inserted": 0,
    }

    repo = BlockPOIRepository(session)

    with log_ingestion_run(session, "block_pois") as run:
        print(f"Starting Block-POI distance calculation (max {max_distance_m}m)...")

        # 1. Fetch all POIs (usually < 1000, so fits in memory)
        # We need them in memory to iterate efficiently for each block
        pois = session.execute(
            select(POI.id, POI.name, POI.latitude, POI.longitude)
            .where(POI.latitude.isnot(None))
            .where(POI.longitude.isnot(None))
        ).all()

        poi_data = [
            {"id": p.id, "lat": float(p.latitude), "lon": float(p.longitude), "name": p.name}
            for p in pois
        ]
        print(f"Loaded {len(poi_data)} POIs into memory.")

        if not poi_data:
            print("No POIs found. Skipping.")
            return summary

        # 2. Fetch all Blocks with coordinates
        blocks_query = (
            select(Block.id, Block.block, Block.street, Block.latitude, Block.longitude)
            .where(Block.latitude.isnot(None))
            .where(Block.longitude.isnot(None))
        )
        blocks = session.execute(blocks_query).all()

        total_blocks = len(blocks)
        print(f"Found {total_blocks} blocks to process.")

        # Pre-calculate degree deltas for bounding box
        # 1 degree lat ~= 111km
        # 1 degree lon ~= 111km * cos(lat)
        lat_delta = max_distance_m / 111320.0
        # Use approx Singapore latitude (1.35) for lon_delta scaling
        # cos(1.35 deg) is approx 0.9997, cos(radians(1.35)) is approx 0.9997
        # Actually cos(1.35 deg) ~ 1. so strict conversion:
        # 111320 * cos(1.35 * pi / 180)
        singapore_lat_rad = math.radians(1.35)
        lon_scale = 111320.0 * math.cos(singapore_lat_rad)
        lon_delta = max_distance_m / lon_scale

        # 3. Process blocks and collect ALL distance records
        all_distance_records = []

        for idx, block in enumerate(blocks):
            block_lat = float(block.latitude)
            block_lon = float(block.longitude)

            # Bounding box filter
            min_lat, max_lat = block_lat - lat_delta, block_lat + lat_delta
            min_lon, max_lon = block_lon - lon_delta, block_lon + lon_delta

            for poi in poi_data:
                # Fast bounding box check
                if not (min_lat <= poi["lat"] <= max_lat and min_lon <= poi["lon"] <= max_lon):
                    continue

                # Precise distance check
                dist = calculate_haversine_distance(block_lat, block_lon, poi["lat"], poi["lon"])

                summary["distances_calculated"] += 1

                if dist <= max_distance_m:
                    # Collect record instead of upserting immediately
                    all_distance_records.append(
                        {
                            "block_id": block.id,
                            "poi_id": poi["id"],
                            "distance_m": dist,
                        }
                    )

            summary["blocks_processed"] += 1

            # Log progress
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{total_blocks} blocks...")

        # 4. Perform batched bulk upsert for ALL records
        print(f"Upserting {len(all_distance_records)} distance records in batches...")

        if all_distance_records:
            # Process in smaller batches with intermediate commits to avoid timeout
            batch_size = 5000
            total_records = len(all_distance_records)
            total_inserted = 0

            for i in range(0, total_records, batch_size):
                batch = all_distance_records[i : i + batch_size]
                inserted_count = repo.bulk_upsert_all_distances(batch)
                total_inserted += inserted_count

                # Commit after each batch to prevent transaction timeout
                session.commit()

                # Log progress
                print(f"  Upserted {min(i + batch_size, total_records)}/{total_records} records...")

            summary["records_inserted"] = total_inserted
        else:
            # Final commit if no records
            session.commit()

        run.rows_processed = summary["records_inserted"]
        print(f"Block-POI distance calculation complete: {summary}")

    return summary
