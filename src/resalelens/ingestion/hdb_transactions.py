"""HDB resale transactions ingestion from data.gov.sg."""

import os
import time
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..models import Transaction
from .utils import (
    fetch_json_with_retry,
    log_ingestion_run,
    normalize_street_name,
    parse_date,
    validate_transaction_record,
)


def ingest_hdb_transactions(session: Session, incremental: bool = False) -> dict[str, int]:
    """
    Ingest HDB resale transactions from data.gov.sg API using bulk upsert.

    Fetches HDB resale transaction records from data.gov.sg API (paginated),
    validates and parses records, and bulk upserts to the transactions table using
    PostgreSQL's INSERT ... ON CONFLICT for optimal performance.

    Args:
        session: SQLAlchemy session
        incremental: If True, only fetch records newer than the latest transaction date.
                    If False (default), fetch all records (full refresh).

    Returns:
        Dictionary with ingestion summary:
        - total_fetched: Total records fetched from API
        - inserted: Number of new records inserted (or upserted)
        - updated: Number of existing records updated (always 0 with bulk upsert)
        - skipped: Number of invalid/duplicate records skipped
        - errors: Number of records that failed to process
        - incremental: Whether incremental mode was used
        - since_date: Start date for incremental sync (if applicable)

    Raises:
        ValueError: If required environment variables are missing
        Exception: If ingestion fails critically
    """
    # Get configuration from environment
    api_url = os.getenv("DATA_GOV_SG_API_URL", "https://data.gov.sg/api/action/datastore_search")
    resource_id = os.getenv("DATA_GOV_SG_RESOURCE_ID")

    if not resource_id:
        raise ValueError(
            "DATA_GOV_SG_RESOURCE_ID environment variable is required for HDB transactions ingestion"
        )

    retry_count = int(os.getenv("INGESTION_RETRY_COUNT", "3"))
    # Rate limiting configuration
    requests_per_minute = int(os.getenv("DATA_GOV_SG_REQUESTS_PER_MINUTE", "60"))  # Conservative default
    delay_between_requests = 60.0 / requests_per_minute if requests_per_minute > 0 else 1.0
    max_records = int(os.getenv("INGESTION_MAX_RECORDS", "0"))  # 0 = no limit

    # Incremental sync: determine start date
    since_date = None
    if incremental:
        # Get the latest transaction date from the database
        max_date = session.query(func.max(Transaction.date)).scalar()
        if max_date:
            since_date = max_date
            print(f"📅 Incremental sync: fetching records since {since_date}")
        else:
            print("ℹ️  No existing data found, falling back to full refresh")
            incremental = False  # No data yet, do full refresh

    summary = {
        "total_fetched": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "incremental": incremental,
        "since_date": str(since_date) if since_date else None,
    }

    with log_ingestion_run(session, "hdb_transactions") as run:
        # Fetch all records with pagination
        offset = 0
        limit = 1000  # Fetch 1000 records per page
        has_more = True

        print(f"Starting HDB transactions ingestion from {api_url}")

        while has_more:
            print(f"Fetching records {offset} to {offset + limit}...")

            # Fetch page of records
            try:
                response = fetch_json_with_retry(
                    url=api_url,
                    params={
                        "resource_id": resource_id,
                        "limit": limit,
                        "offset": offset,
                    },
                    max_retries=retry_count,
                )

                result = response.get("result", {})
                records = result.get("records", [])
                total_records = result.get("total", 0)

                print(f"Fetched {len(records)} records (total available: {total_records})")

                # Prepare batch for bulk upsert
                transactions_batch = []
                for record in records:
                    try:
                        # Validate record
                        if not validate_transaction_record(record):
                            summary["skipped"] += 1
                            continue

                        # Parse date
                        date_obj = parse_date(record["month"])

                        # Incremental sync: skip records older than since_date
                        if since_date and date_obj.date() <= since_date:
                            summary["skipped"] += 1
                            continue

                        # Add to batch
                        transactions_batch.append({
                            "date": date_obj.date(),
                            "block": record["block"],
                            "street": normalize_street_name(record["street_name"]),
                            "flat_type": record["flat_type"],
                            "storey_range": record["storey_range"],
                            "floor_area_sqm": float(record["floor_area_sqm"]),
                            "price": float(record["resale_price"]),
                            "lease_commence_date": int(record["lease_commence_date"]),
                            "town": record["town"],
                            "flat_model": record["flat_model"],
                            "latitude": None,  # Will be populated by blocks ingestion
                            "longitude": None,
                            "ingestion_run_id": run.id,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        })

                    except Exception as e:
                        print(f"Error processing record: {e}")
                        summary["errors"] += 1
                        continue

                # Bulk upsert the entire batch
                if transactions_batch:
                    # Deduplicate within the batch to avoid PostgreSQL cardinality violation
                    # (same record appearing twice in one INSERT)
                    seen_keys = set()
                    deduplicated_batch = []

                    for txn in transactions_batch:
                        # Create unique key from constraint columns
                        key = (
                            txn["block"],
                            txn["street"],
                            txn["flat_type"],
                            txn["date"],
                            txn["storey_range"],
                            txn["floor_area_sqm"],
                        )

                        if key not in seen_keys:
                            seen_keys.add(key)
                            deduplicated_batch.append(txn)
                        else:
                            summary["skipped"] += 1  # Count as skipped duplicate

                    print(f"Bulk upserting {len(deduplicated_batch)} records (skipped {len(transactions_batch) - len(deduplicated_batch)} in-batch duplicates)...")

                    stmt = insert(Transaction).values(deduplicated_batch)

                    # On conflict, update the existing record
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['block', 'street', 'flat_type', 'date', 'storey_range', 'floor_area_sqm'],
                        set_={
                            'price': stmt.excluded.price,
                            'lease_commence_date': stmt.excluded.lease_commence_date,
                            'town': stmt.excluded.town,
                            'flat_model': stmt.excluded.flat_model,
                            'ingestion_run_id': stmt.excluded.ingestion_run_id,
                            'updated_at': stmt.excluded.updated_at,
                        }
                    )

                    session.execute(stmt)
                    session.commit()

                    # Track inserted count (we can't distinguish inserts vs updates with bulk upsert)
                    summary["inserted"] += len(deduplicated_batch)
                    print("✅ Batch upserted successfully")

                summary["total_fetched"] += len(records)

                # Rate limiting: pause between API requests
                if has_more and delay_between_requests > 0:
                    print(f"Rate limiting: sleeping {delay_between_requests:.2f}s before next request")
                    time.sleep(delay_between_requests)

                # Check if there are more records
                offset += limit
                has_more = offset < total_records

                # Check if we've hit max records limit
                if max_records > 0 and summary["total_fetched"] >= max_records:
                    print(f"Max records limit reached ({max_records}). Stopping ingestion.")
                    has_more = False

            except Exception as e:
                print(f"Error fetching records at offset {offset}: {e}")
                raise

        # Update ingestion run summary
        run.rows_processed = summary["total_fetched"]

        print(f"HDB transactions ingestion complete: {summary}")

    return summary

