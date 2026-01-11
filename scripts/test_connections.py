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


def test_onemap_api() -> bool:
    """Test OneMap geocoding API connection."""
    print("\n" + "=" * 60)
    print("Testing OneMap Geocoding API...")
    print("=" * 60)

    # Check for pre-obtained token first
    token = os.getenv("ONEMAP_API_TOKEN")

    if token:
        print("Using pre-obtained API token from ONEMAP_API_TOKEN")
        print(f"Token: {token[:20]}..." if len(token) > 20 else "Token: (short)")
    else:
        # Fall back to email/password auth
        auth_url = "https://www.onemap.gov.sg/api/auth/post/getToken"
        email = os.getenv("ONEMAP_EMAIL")
        password = os.getenv("ONEMAP_PASSWORD")

        if not email or not password:
            print("❌ ERROR: Neither ONEMAP_API_TOKEN nor ONEMAP_EMAIL/PASSWORD set")
            print("\n⚠️  To fix (choose one method):")
            print("   Method 1 (Recommended): Use your existing token")
            print("      ONEMAP_API_TOKEN=your-token-here")
            print("\n   Method 2: Use email/password (if working)")
            print("      ONEMAP_EMAIL=your-email")
            print("      ONEMAP_PASSWORD=your-password")
            print("\n   Get token from: https://www.onemap.gov.sg/apidocs/")
            return False

        print(f"Email: {email}")
        print("Password: *** (hidden)")

        try:
            print("\n1. Getting API token via email/password...")
            response = fetch_json_with_retry(
                url=auth_url,
                params={"email": email, "password": password},
                max_retries=1,
            )

            token = response.get("access_token")
            if not token:
                print("❌ ERROR: No token received. Check credentials.")
                return False

            print(f"   ✅ Token received: {token[:20]}...")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            if "401" in str(e) or "403" in str(e) or "Unauthorized" in str(e) or "Forbidden" in str(e):
                print("\n⚠️  Authentication failed. Try using ONEMAP_API_TOKEN instead:")
                print("   1. Get your token from OneMap dashboard")
                print("   2. Add to .env.local: ONEMAP_API_TOKEN=your-token")
                print("   3. Comment out or remove ONEMAP_EMAIL and ONEMAP_PASSWORD")
            return False

    # Test geocoding with the token
    try:
        print("\n2. Testing geocoding with sample address...")
        search_url = os.getenv(
            "ONEMAP_API_URL", "https://www.onemap.gov.sg/api/common/elastic/search"
        )
        test_address = "1 Beach Road, Singapore"

        geo_response = fetch_json_with_retry(
            url=search_url,
            params={
                "searchVal": test_address,
                "returnGeom": "Y",
                "getAddrDetails": "Y",  # Required parameter per OneMap docs
            },
            headers={"Authorization": token},  # Token without 'Bearer' prefix
            max_retries=1,
        )

        results = geo_response.get("results", [])
        if results:
            first = results[0]
            print("   ✅ Geocoding successful!")
            print(f"   Address: {first.get('ADDRESS')}")
            print(f"   Latitude: {first.get('LATITUDE')}")
            print(f"   Longitude: {first.get('LONGITUDE')}")
        else:
            print(f"   ⚠️  No results for '{test_address}' (API works but no match)")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_database_connection() -> bool:
    """Test database connection."""
    print("\n" + "=" * 60)
    print("Testing Database Connection...")
    print("=" * 60)

    try:
        from sqlalchemy import text

        from resalelens.database import SessionLocal

        # Test connection
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        db.close()

        database_url = os.getenv("DATABASE_URL", "")

        if not database_url:
            print("❌ ERROR: DATABASE_URL not set")
            print("\n📝 To fix:")
            print("   1. Set DATABASE_URL in .env.local")
            print("   2. Use Supabase connection string")
            print("   3. See docs/technical/supabase_setup.md")
            return False

        # Should be PostgreSQL (Supabase)
        if database_url.startswith("postgresql"):
            print("✅ Database connection successful!")
            print("   Type: PostgreSQL (Supabase)")
            # Don't print full URL for security
            print("   Connected to Supabase")
        else:
            print(f"⚠️  WARNING: Expected PostgreSQL, got: {database_url[:20]}...")
            print("   Supabase (PostgreSQL) is required for this application")
            print("   See docs/technical/supabase_setup.md for setup")
            return False

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n📝 Troubleshooting:")
        print("   1. Check DATABASE_URL format in .env.local")
        print("   2. Verify Supabase project is accessible")
        print("   3. Run migrations: uv run alembic upgrade head")
        return False


def main() -> None:
    """Run all connection tests."""
    print("\n🔧 ResaleLens API Connection Tests\n")

    results = {
        "data.gov.sg": test_data_gov_sg(),
        "OneMap": test_onemap_api(),
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
        print("      curl -X POST 'http://localhost:8000/admin/ingestion/trigger?dataset=hdb_transactions'")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Fix the issues above before running ingestion.")
        sys.exit(1)


if __name__ == "__main__":
    main()
