"""
Connection test script for data.gov.sg and OneMap APIs.

Tests API connectivity and credentials before running full ingestion.
Run this before first ingestion to verify setup.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

from resalelens.ingestion.utils import fetch_json_with_retry


def test_data_gov_sg() -> bool:
    """Test data.gov.sg API connection."""
    print("=" * 60)
    print("Testing data.gov.sg HDB Resale Prices API...")
    print("=" * 60)

    api_url = os.getenv("DATA_GOV_SG_API_URL", "https://data.gov.sg/api/action/datastore_search")
    resource_id = os.getenv("DATA_GOV_SG_RESOURCE_ID")

    if not resource_id:
        print("❌ ERROR: DATA_GOV_SG_RESOURCE_ID not set in .env.local")
        return False

    try:
        print(f"API URL: {api_url}")
        print(f"Resource ID: {resource_id}")
        print("\nFetching sample data (limit=5)...")

        response = fetch_json_with_retry(
            url=api_url,
            params={"resource_id": resource_id, "limit": 5},
            max_retries=1,
        )

        result = response.get("result", {})
        total = result.get("total", 0)
        records = result.get("records", [])

        print("\n✅ SUCCESS!")
        print(f"   Total records available: {total:,}")
        print(f"   Sample records fetched: {len(records)}")

        if records:
            print("\n📋 Sample record:")
            sample = records[0]
            print(f"   Month: {sample.get('month')}")
            print(f"   Town: {sample.get('town')}")
            print(f"   Block: {sample.get('block')} {sample.get('street_name')}")
            print(f"   Flat Type: {sample.get('flat_type')}")
            print(f"   Price: ${sample.get('resale_price')}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main() -> None:
    """Run all connection tests."""
    print("\n🔧 ResaleLens API Connection Tests\n")

    results = {
        "data.gov.sg": test_data_gov_sg(),
        "Database": test_database_connection(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = all(results.values())

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run ingestion.")
        print("\nNext steps:")
        print("   1. Start server: uv run uvicorn src.resalelens.main:app --reload")
        print("   2. Trigger ingestion:")
        print(
            "      curl -X POST 'http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions'"
        )
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Fix the issues above before running ingestion.")
        sys.exit(1)


if __name__ == "__main__":
    main()
