#!/usr/bin/env python3
"""Test script to debug geocoding failures."""

from resalelens.database import SessionLocal
from resalelens.ingestion.hdb_blocks import OneMapClient
from resalelens.ingestion.utils import fetch_json_with_retry
from resalelens.models import Block

# Get a sample of failed blocks
db = SessionLocal()
failed_blocks = db.query(Block).filter(
    Block.latitude.is_(None),
    Block.last_updated.isnot(None)
).limit(10).all()

print(f"Testing {len(failed_blocks)} failed blocks\n")
print("=" * 80)

client = OneMapClient()
success_count = 0
fail_count = 0

for block_obj in failed_blocks:
    full_address = f"{block_obj.block} {block_obj.street}"

    # Test direct API call
    try:
        response = fetch_json_with_retry(
            url="https://www.onemap.gov.sg/api/common/elastic/search",
            params={
                "searchVal": full_address,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
            },
            max_retries=1,
        )
        api_results = response.get("results", [])
        api_success = len(api_results) > 0
    except Exception as e:
        api_success = False
        api_error = str(e)

    # Test OneMapClient method
    try:
        client_result = client.geocode_address(full_address)
        client_success = client_result is not None
    except Exception as e:
        client_success = False
        client_error = str(e)

    # Report
    print(f"\nAddress: {full_address}")
    print(f"  Direct API:    {'✅ SUCCESS' if api_success else '❌ FAILED'}")
    if not api_success and 'api_error' in locals():
        print(f"    Error: {api_error}")
    print(f"  Client method: {'✅ SUCCESS' if client_success else '❌ FAILED'}")
    if not client_success and 'client_error' in locals():
        print(f"    Error: {client_error}")

    if api_success and not client_success:
        print("  ⚠️  API works but client method fails!")
        fail_count += 1
    elif client_success:
        success_count += 1

print("\n" + "=" * 80)
print("\nSummary:")
print(f"  Addresses that work with client: {success_count}/{len(failed_blocks)}")
print(f"  API works but client fails: {fail_count}/{len(failed_blocks)}")

db.close()
