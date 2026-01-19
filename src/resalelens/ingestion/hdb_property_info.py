"""HDB Property Information ingestion from data.gov.sg."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.orm import Session

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
    resource_id = os.getenv("DATA_GOV_SG_PROPERTY_INFO_ID", "d_17f5382f26140b1fdae0ba2ef6239d2f")
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

        # Collect all updates for bulk processing
        updates = []

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

                # Collect updates instead of modifying ORM objects
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

                        # Parse new values
                        new_data = {
                            "max_floor_lvl": parse_int(record.get("max_floor_lvl")),
                            "year_completed": parse_int(record.get("year_completed")),
                            "total_dwelling_units": parse_int(record.get("total_dwelling_units")),
                            "residential": parse_bool(record.get("residential")),
                            "commercial": parse_bool(record.get("commercial")),
                            "market_hawker": parse_bool(record.get("market_hawker")),
                            "multistorey_carpark": parse_bool(record.get("multistorey_carpark")),
                            "precinct_pavilion": parse_bool(record.get("precinct_pavilion")),
                            "miscellaneous": parse_bool(record.get("miscellaneous")),
                            "room_1_sold": parse_int(record.get("1room_sold")),
                            "room_2_sold": parse_int(record.get("2room_sold")),
                            "room_3_sold": parse_int(record.get("3room_sold")),
                            "room_4_sold": parse_int(record.get("4room_sold")),
                            "room_5_sold": parse_int(record.get("5room_sold")),
                            "exec_sold": parse_int(record.get("exec_sold")),
                            "multigen_sold": parse_int(record.get("multigen_sold")),
                            "studio_apartment_sold": parse_int(record.get("studio_apartment_sold")),
                            "room_1_rental": parse_int(record.get("1room_rental")),
                            "room_2_rental": parse_int(record.get("2room_rental")),
                            "room_3_rental": parse_int(record.get("3room_rental")),
                            "other_room_rental": parse_int(record.get("other_room_rental")),
                        }

                        # Check if any field has changed (incremental optimization)
                        has_changes = False
                        for field, new_value in new_data.items():
                            old_value = getattr(block, field)
                            if old_value != new_value:
                                has_changes = True
                                break

                        # Only add to updates if data has changed
                        if has_changes:
                            update_data = {
                                "id": block.id,
                                **new_data,
                                "last_updated": datetime.utcnow(),
                            }
                            updates.append(update_data)

                        summary["matched"] += 1

                    except Exception as e:
                        print(f"Error processing property record: {e}")
                        summary["errors"] += 1
                        continue

                # Check if we've fetched all records
                if offset + len(records) >= total:
                    break

                offset += limit

            except Exception as e:
                print(f"Error fetching property data at offset {offset}: {e}")
                summary["errors"] += 1
                break

        # Perform bulk update in batches
        if updates:
            skipped = summary["matched"] - len(updates)
            print(
                f"\nPerforming bulk update of {len(updates)} changed blocks (skipped {skipped} unchanged)..."
            )
            batch_size = 1000
            total_updates = len(updates)

            for i in range(0, total_updates, batch_size):
                batch = updates[i : i + batch_size]
                session.bulk_update_mappings(Block, batch)
                session.commit()

                # Progress logging
                processed = min(i + batch_size, total_updates)
                print(f"  ✓ Updated {processed}/{total_updates} blocks...")

            print(
                f"Bulk update complete: {total_updates} blocks updated, {skipped} skipped (no changes)"
            )
        else:
            print("\n✅ No changes detected - all blocks are up to date!")
            # Final commit if no updates
            session.commit()

        # Update ingestion run
        run.rows_processed = summary["total_fetched"]

        print(f"HDB property information ingestion complete: {summary}")

    return summary
