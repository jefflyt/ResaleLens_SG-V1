"""HDB blocks ingestion with geocoding from OneMap API."""

from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from ..api.onemap import OneMapClient
from ..data.repositories import BlockRepository
from ..models import Block, Transaction
from .utils import log_ingestion_run, normalize_street_name

# OneMapClient class moved to src/resalelens/api/onemap.py



def ingest_hdb_blocks(
    session: Session, batch_size: int | None = None, skip_existing: bool = True
) -> dict[str, int]:
    """
    Ingest HDB block metadata by geocoding unique blocks from transactions.

    This function extracts unique block addresses from the transactions table
    and geocodes them using the OneMap API. It's designed to be run once to
    populate the blocks table with geocoded coordinates.

    Args:
        session: Database session
        batch_size: Optional limit on number of blocks to process (for incremental runs)
        skip_existing: If True, skip blocks that already have coordinates (default: True)

    Returns:
        Dictionary with ingestion statistics:
        - total_blocks: Total unique blocks processed
        - inserted: Number of new blocks inserted
        - updated: Number of existing blocks updated
        - geocoded: Number of blocks successfully geocoded
        - geocoding_failed: Number of blocks where geocoding failed
        Exception: If ingestion fails critically
    """
    repo = BlockRepository(session)
    onemap_client = OneMapClient()

    summary = {
        "total_blocks": 0,
        "inserted": 0,
        "updated": 0,
        "geocoded": 0,
        "geocoding_failed": 0,
    }

    with log_ingestion_run(session, "hdb_blocks") as run:
        print("Extracting unique blocks from transactions...")

        # Extract unique blocks from transactions
        unique_blocks = (
            session.query(
                distinct(Transaction.block),
                Transaction.street,
                Transaction.town,
                Transaction.lease_commence_date,
            )
            .group_by(Transaction.block, Transaction.street, Transaction.town, Transaction.lease_commence_date)
            .all()
        )
        summary["total_blocks"] = len(unique_blocks)
        print(f"Found {summary['total_blocks']} unique blocks to process")

        # Apply batch size limit if specified
        if batch_size:
            unique_blocks = unique_blocks[:batch_size]
            print(f"Batch processing: limiting to {batch_size} blocks")

        # Process each block
        processed_count = 0
        for _idx, (block, street, town, lease_commence_date) in enumerate(unique_blocks):
            try:
                # Check if block already exists
                existing = repo.get_by_block_and_street(block, street)

                # Skip if block already has coordinates and skip_existing is True
                if skip_existing and existing and existing.latitude is not None:
                    print(f"Skipping {block} {street} (already geocoded)")
                    continue

                # Rate limiting: respect OneMap API limits
                if processed_count > 0 and processed_count % 100 == 0:
                    print(f"Processed {processed_count}/{len(unique_blocks)} blocks. Pausing for rate limit...")
                    time.sleep(2)  # 2-second pause every 100 requests

                # Geocode address
                full_address = f"{block} {street}"
                geocode_result = onemap_client.geocode_address(full_address)

                if geocode_result:
                    latitude = geocode_result["latitude"]
                    longitude = geocode_result["longitude"]
                    summary["geocoded"] += 1
                else:
                    latitude = None
                    longitude = None
                    summary["geocoding_failed"] += 1
                    print(f"Warning: Geocoding failed for {full_address}")

                if existing:
                    # Update existing block
                    existing.latitude = latitude
                    existing.longitude = longitude
                    existing.lease_commence_year = lease_commence_date
                    existing.last_updated = datetime.utcnow()
                    repo.update(existing)
                    summary["updated"] += 1
                else:
                    # Create new block
                    block_obj = Block(
                        block=block,
                        street=normalize_street_name(street),
                        town=town,
                        latitude=latitude,
                        longitude=longitude,
                        lease_commence_year=lease_commence_date,
                        last_updated=datetime.utcnow(),
                    )
                    session.add(block_obj)
                    summary["inserted"] += 1

                # Increment processed count
                processed_count += 1

                # Commit in batches
                if processed_count % 100 == 0:
                    session.commit()
                    print(f"Batch committed: {processed_count}/{len(unique_blocks)}")

            except Exception as e:
                print(f"Error processing block {block} {street}: {e}")
                continue

        # Final commit
        session.commit()

        # Update ingestion run summary
        run.rows_processed = summary["total_blocks"]

        print(f"HDB blocks ingestion complete: {summary}")

    return summary
