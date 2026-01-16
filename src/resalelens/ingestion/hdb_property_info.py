"""HDB Property Information ingestion from data.gov.sg."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.orm import Session

from ..data.repositories import BlockRepository
from ..models import Block
from .utils import fetch_json_with_retry, log_ingestion_run, normalize_street_name


def parse_bool(value: str) -> bool:
    """Parse Y/N string to boolean."""
    return value.upper() == "Y" if value else False


def parse_int(value: str) -> int | None:
    """Parse string to integer, return None if invalid."""
    try:
        return int(value) if value and value.strip() else None
    except (ValueError, AttributeError):
        return None


def ingest_hdb_property_info(session: Session) -> dict[str, int]:
    """
    Ingest HDB property information from data.gov.sg API.

    Enriches existing blocks with official HDB property data including:
    - Building characteristics (floors, year built, total units)
    - Facility flags (commercial, hawker, carpark, etc.)
    - Unit mix distribution

    Args:
        session: SQLAlchemy session

    Returns:
        Dictionary with ingestion summary:
        - total_fetched: Total property records fetched
        - matched: Number of blocks matched and updated
        - unmatched: Number of property records not matched to blocks
        - errors: Number of records that failed to process
    """
    resource_id = "d_17f5382f26140b1fdae0ba2ef6239d2f"
    api_url = os.getenv("DATA_GOV_SG_API_URL", "https://data.gov.sg/api/action/datastore_search")

    summary = {
        "total_fetched": 0,
        "matched": 0,
        "unmatched": 0,
        "errors": 0,
    }

    with log_ingestion_run(session, "hdb_property_info") as run:
        print("Pre-loading blocks from database...")
        # Load all blocks into memory for fast matching
        # Map (block, street) -> Block object
        all_blocks_list = session.query(Block).all()
        blocks_map = {(b.block, b.street): b for b in all_blocks_list}
        # Fallback map using normalized street names: (block, normalized_street) -> Block object
        normalized_map = {(b.block, normalize_street_name(b.street)): b for b in all_blocks_list}

        print(f"Loaded {len(blocks_map)} blocks. Fetching HDB property information from {api_url}")

        # Fetch all records (paginated)
        offset = 0
        limit = 5000  # Larger limit for fewer requests

        while True:
            try:
                response = fetch_json_with_retry(
                    url=api_url,
                    params={
                        "resource_id": resource_id,
                        "limit": limit,
                        "offset": offset,
                    },
                    max_retries=3,
                )

                result = response.get("result", {})
                records = result.get("records", [])
                total = int(result.get("total", 0))

                if not records:
                    break

                print(f"Processing {len(records)} property records (offset {offset}/{total})...")

                for record in records:
                    try:
                        summary["total_fetched"] += 1

                        # Extract block and street
                        blk_no = record.get("blk_no", "").strip()
                        street = record.get("street", "").strip()

                        if not blk_no or not street:
                            summary["errors"] += 1
                            continue

                        # Try to find matching block
                        # First try exact match
                        block = blocks_map.get((blk_no, street))

                        # If no exact match, try normalized street name
                        if not block:
                            normalized_street = normalize_street_name(street)
                            block = normalized_map.get((blk_no, normalized_street))

                        if not block:
                            summary["unmatched"] += 1
                            continue


                        # Update block with property info
                        block.max_floor_lvl = parse_int(record.get("max_floor_lvl"))
                        block.year_completed = parse_int(record.get("year_completed"))
                        block.total_dwelling_units = parse_int(record.get("total_dwelling_units"))

                        # Facility flags
                        block.residential = parse_bool(record.get("residential"))
                        block.commercial = parse_bool(record.get("commercial"))
                        block.market_hawker = parse_bool(record.get("market_hawker"))
                        block.multistorey_carpark = parse_bool(record.get("multistorey_carpark"))
                        block.precinct_pavilion = parse_bool(record.get("precinct_pavilion"))
                        block.miscellaneous = parse_bool(record.get("miscellaneous"))

                        # Unit mix - sold
                        block.room_1_sold = parse_int(record.get("1room_sold"))
                        block.room_2_sold = parse_int(record.get("2room_sold"))
                        block.room_3_sold = parse_int(record.get("3room_sold"))
                        block.room_4_sold = parse_int(record.get("4room_sold"))
                        block.room_5_sold = parse_int(record.get("5room_sold"))
                        block.exec_sold = parse_int(record.get("exec_sold"))
                        block.multigen_sold = parse_int(record.get("multigen_sold"))
                        block.studio_apartment_sold = parse_int(record.get("studio_apartment_sold"))

                        # Unit mix - rental
                        block.room_1_rental = parse_int(record.get("1room_rental"))
                        block.room_2_rental = parse_int(record.get("2room_rental"))
                        block.room_3_rental = parse_int(record.get("3room_rental"))
                        block.other_room_rental = parse_int(record.get("other_room_rental"))

                        block.last_updated = datetime.utcnow()

                        summary["matched"] += 1

                    except Exception as e:
                        print(f"Error processing property record: {e}")
                        summary["errors"] += 1
                        continue

                # Commit batch
                session.commit()
                print(f"Batch committed: {offset + len(records)}/{total}")

                # Check if we've fetched all records
                if offset + len(records) >= total:
                    break

                offset += limit

            except Exception as e:
                print(f"Error fetching property data at offset {offset}: {e}")
                summary["errors"] += 1
                break

        # Update ingestion run
        run.rows_processed = summary["total_fetched"]

        print(f"HDB property information ingestion complete: {summary}")

    return summary
