#!/usr/bin/env python3
"""Script to run complete weekly ingestion sequence and generate report."""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resalelens.database import SessionLocal
from src.resalelens.ingestion import (
    ingest_block_pois,
    ingest_hdb_postal_codes,
    ingest_hdb_property_info,
    ingest_hdb_transactions,
    ingest_pois,
    ingest_transaction_backfill,
)


def run_weekly_ingestion():
    """Run complete weekly ingestion sequence and track performance."""

    print("\n" + "=" * 80)
    print("WEEKLY INGESTION SEQUENCE TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []
    total_start = time.time()

    # Define ingestion sequence
    jobs = [
        ("HDB Transactions", ingest_hdb_transactions, {}),
        ("Transaction Backfill", ingest_transaction_backfill, {}),
        ("POIs", ingest_pois, {}),
        ("HDB Postal Codes", ingest_hdb_postal_codes, {}),
        ("HDB Property Info", ingest_hdb_property_info, {}),
        ("Block-POI Distances", ingest_block_pois, {}),
    ]

    for idx, (name, func, kwargs) in enumerate(jobs, 1):
        print(f"\n{'=' * 80}")
        print(f"[{idx}/6] {name}")
        print(f"{'=' * 80}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

        db = SessionLocal()
        try:
            start_time = time.time()
            summary = func(db, **kwargs)
            duration = time.time() - start_time

            results.append(
                {"name": name, "status": "✅ SUCCESS", "duration": duration, "summary": summary}
            )

            print(f"\n✅ {name} completed in {duration:.2f}s ({duration / 60:.2f}m)")
            print(f"Summary: {summary}")

        except Exception as e:
            duration = time.time() - start_time
            results.append(
                {"name": name, "status": "❌ FAILED", "duration": duration, "error": str(e)}
            )
            print(f"\n❌ {name} failed after {duration:.2f}s")
            print(f"Error: {e}")

        finally:
            db.close()

    total_duration = time.time() - total_start

    # Generate report
    print("\n" + "=" * 80)
    print("INGESTION REPORT")
    print("=" * 80)
    print(f"Total Duration: {total_duration:.2f}s ({total_duration / 60:.2f}m)")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"{'Job':<30} {'Status':<15} {'Duration':<20}")
    print("-" * 80)

    for result in results:
        duration_str = f"{result['duration']:.2f}s ({result['duration'] / 60:.2f}m)"
        print(f"{result['name']:<30} {result['status']:<15} {duration_str:<20}")

    print("-" * 80)
    print(f"{'TOTAL':<30} {'':<15} {total_duration:.2f}s ({total_duration / 60:.2f}m)")
    print("=" * 80)

    # Detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Status: {result['status']}")
        print(f"  Duration: {result['duration']:.2f}s")
        if "summary" in result:
            print(f"  Summary: {result['summary']}")
        if "error" in result:
            print(f"  Error: {result['error']}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return results, total_duration


if __name__ == "__main__":
    run_weekly_ingestion()
