"""HDB blocks ingestion with geocoding from OneMap API."""

import os
import time
from datetime import datetime

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from ..data.repositories import BlockRepository
from ..models import Block, Transaction
from .utils import fetch_json_with_retry, log_ingestion_run


class OneMapClient:
    """Client for OneMap geocoding API with token management."""

    def __init__(self) -> None:
        """Initialize OneMap client."""
        self.api_url = os.getenv(
            "ONEMAP_API_URL", "https://www.onemap.gov.sg/api/common/elastic/search"
        )
        self.auth_url = "https://www.onemap.gov.sg/api/auth/post/getToken"
        
        # Support both token-based and email/password auth
        self.token = os.getenv("ONEMAP_API_TOKEN")  # Pre-obtained token
        self.email = os.getenv("ONEMAP_EMAIL")
        self.password = os.getenv("ONEMAP_PASSWORD")

        self.token_expiry: datetime | None = None
        self.request_count = 0
        self.max_requests_per_token = 240  # Safety margin (250 limit)

    def _get_token(self) -> str:
        """
        Get or refresh OneMap API token.

        Returns:
            Valid JWT token

        Raises:
            ValueError: If credentials are missing
            Exception: If token request fails
        """
        # If we have a pre-obtained token, use it
        if self.token and os.getenv("ONEMAP_API_TOKEN"):
            print("Using pre-obtained OneMap API token from ONEMAP_API_TOKEN")
            return self.token

        # Otherwise, authenticate with email/password
        if not self.email or not self.password:
            raise ValueError(
                "Either ONEMAP_API_TOKEN or both ONEMAP_EMAIL and ONEMAP_PASSWORD environment variables are required"
            )

        # Check if we need a new token
        needs_token = (
            self.token is None
            or self.token_expiry is None
            or datetime.utcnow() >= self.token_expiry
            or self.request_count >= self.max_requests_per_token
        )

        if needs_token:
            response = fetch_json_with_retry(
                url=self.auth_url,
                params={
                    "email": self.email,
                    "password": self.password,
                },
            )

            self.token = response.get("access_token")
            if not self.token:
                raise Exception("Failed to obtain OneMap API token")

            # Token expires in 3 days, but we'll refresh daily for safety
            self.token_expiry = datetime.utcnow().replace(
                hour=23, minute=59, second=59, microsecond=0
            )
            self.request_count = 0
            print("OneMap API token obtained successfully")

        # Token should now be set
        if not self.token:
            raise Exception("Failed to obtain OneMap API token after refresh")

        return self.token

    def geocode_address(self, address: str) -> dict[str, float] | None:
        """
        Geocode an address using OneMap API.

        Args:
            address: Full address to geocode

        Returns:
            Dictionary with latitude and longitude, or None if geocoding fails
        """
        token = self._get_token()

        try:
            response = fetch_json_with_retry(
                url=self.api_url,
                params={
                    "searchVal": address,
                    "returnGeom": "Y",
                    "getAddrDetails": "Y",  # Required parameter
                },
                headers={"Authorization": token},  # Token without 'Bearer' prefix
                max_retries=2,
            )

            self.request_count += 1

            results = response.get("results", [])
            if not results:
                return None

            # Return first result
            first_result = results[0]
            return {
                "latitude": float(first_result.get("LATITUDE", 0)),
                "longitude": float(first_result.get("LONGITUDE", 0)),
            }

        except Exception as e:
            print(f"Geocoding failed for address '{address}': {e}")
            return None


def ingest_hdb_blocks(session: Session) -> dict[str, int]:
    """
    Ingest HDB blocks by extracting unique blocks from transactions and geocoding.

    Extracts unique (block, street, town) combinations from ingested transactions,
    geocodes addresses using OneMap API, and upserts to the blocks table.

    Args:
        session: SQLAlchemy session

    Returns:
        Dictionary with ingestion summary:
        - total_blocks: Total unique blocks processed
        - inserted: Number of new blocks inserted
        - updated: Number of existing blocks updated
        - geocoded: Number of blocks successfully geocoded
        - geocoding_failed: Number of blocks where geocoding failed

    Raises:
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

        # Process each block
        for idx, (block, street, town, lease_commence_date) in enumerate(unique_blocks):
            try:
                # Rate limiting: respect OneMap API limits
                if idx > 0 and idx % 100 == 0:
                    print(f"Processed {idx}/{summary['total_blocks']} blocks. Pausing for rate limit...")
                    time.sleep(2)  # 2-second pause every 100 requests

                # Check if block already exists
                existing = repo.get_by_block_and_street(block, street)

                # Geocode address
                full_address = f"{block} {street}, Singapore"
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
                        street=street,
                        town=town,
                        latitude=latitude,
                        longitude=longitude,
                        lease_commence_year=lease_commence_date,
                        last_updated=datetime.utcnow(),
                    )
                    session.add(block_obj)
                    summary["inserted"] += 1

                # Commit in batches
                if (idx + 1) % 100 == 0:
                    session.commit()
                    print(f"Batch committed: {idx + 1}/{summary['total_blocks']}")

            except Exception as e:
                print(f"Error processing block {block} {street}: {e}")
                continue

        # Final commit
        session.commit()

        # Update ingestion run summary
        run.rows_processed = summary["total_blocks"]

        print(f"HDB blocks ingestion complete: {summary}")

    return summary
