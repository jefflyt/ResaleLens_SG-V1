"""HDB postal codes ingestion using pattern-based generation.

Strategy:
1. Iterate through all HDB blocks in the database
2. Generate postal codes using Singapore's deterministic pattern:
   - Sector (2 digits, based on Town) + Letter Suffix Code (1 digit) + Block Number (3 digits)
   - Letter Suffix Code: 0 for no suffix, 1=A, 2=B, etc.
3. Update database blocks directly
4. No external API calls required (instant execution)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from ..ingestion.utils import log_ingestion_run
from ..models import Block
from ..utils.postal_code_patterns import generate_hdb_postal_code
from .onemap_client import OneMapClient


def ingest_hdb_postal_codes(
    session: Session, batch_size: int | None = None, skip_existing: bool = True
) -> dict[str, int]:
    """
    Ingest HDB postal codes using pattern-based generation.

    Singapore postal codes for HDB blocks follow a deterministic pattern,
    allowing us to generate them without external API calls.

    This function also attempts to fetch geolocation (Lat/Lon) from OneMap
    associated with the generated postal code.

    Pattern: Postal Sector (2 digits) + Letter Suffix Code (1 digit) + Block Number (3 digits)

    Args:
        session: Database session
        batch_size: Optional limit on number of blocks to process (mostly for testing)
        skip_existing: If True, skip blocks with postal codes (default: True)

    Returns:
        Dictionary with ingestion statistics
    """
    summary = {
        "total_blocks": 0,
        "blocks_processed": 0,
        "postal_codes_generated": 0,
        "geocoded": 0,
        "no_pattern_match": 0,
        "skipped_existing": 0,
    }

    with log_ingestion_run(session, "hdb_postal_codes") as run:
        print("Starting pattern-based HDB postal code ingestion...")

        # Initialize OneMap client for geolocation
        onemap_client = OneMapClient()

        # Step 1: Fetch blocks from database
        query = select(Block)
        if skip_existing:
            query = query.where(Block.postal_code.is_(None))

        if batch_size:
            query = query.limit(batch_size)
            print(f"Batch processing: limiting to {batch_size} blocks")

        blocks = session.scalars(query).all()
        summary["total_blocks"] = len(blocks)
        print(f"Found {summary['total_blocks']} blocks to process")

        # Step 2: Generate postal codes
        updates = []

        for block in blocks:
            # Generate postal code candidates
            candidates = generate_hdb_postal_code(block.block, block.town)

            if not candidates:
                summary["no_pattern_match"] += 1
                continue

            # Use the first candidate (usually the correct one)
            # In rare cases of ambiguous sectors, this picks the first sector in the list
            postal_code = candidates[0]
            postal_sector = postal_code[:2]

            update_data = {
                "id": block.id,
                "postal_code": postal_code,
                "postal_sector": postal_sector,
                "last_updated": datetime.utcnow(),
            }

            # Geolocation: Fetch Lat/Lon if missing
            if not block.latitude or not block.longitude:
                try:
                    # Search by postal code - highly accurate
                    results = onemap_client.fetch_poi_search(postal_code)
                    if results:
                        # Take first result
                        res = results[0]
                        lat = res.get("LATITUDE")
                        lon = res.get("LONGITUDE")

                        if lat and lon and lat != "NIL" and lon != "NIL":
                            update_data["latitude"] = float(lat)
                            update_data["longitude"] = float(lon)
                            summary["geocoded"] += 1
                except Exception as e:
                    print(f"Geolocation failed for {postal_code}: {e}")

            # Prepare update
            updates.append(update_data)

            summary["postal_codes_generated"] += 1

        summary["blocks_processed"] = len(updates)

        # Step 3: Bulk update database
        if updates:
            print(f"Updating {len(updates)} blocks in database...")

            # Process in batches to avoid database timeouts
            update_batch_size = 1000
            for i in range(0, len(updates), update_batch_size):
                batch = updates[i : i + update_batch_size]
                session.bulk_update_mappings(inspect(Block), batch)  # type: ignore[arg-type]
                session.commit()
                print(
                    f"  ✓ Processed batch {i // update_batch_size + 1}/{(len(updates) + update_batch_size - 1) // update_batch_size}"
                )

            # Verify final commit
            session.commit()

        run.rows_processed = summary["blocks_processed"]

        print("\n✅ HDB postal codes ingestion complete:")
        print(f"  - Total blocks found: {summary['total_blocks']}")
        print(f"  - Postal codes generated: {summary['postal_codes_generated']}")
        print(f"  - No pattern match: {summary['no_pattern_match']}")

    return summary
