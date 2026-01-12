"""OneMap API Client."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from resalelens.ingestion.utils import fetch_json_with_retry, normalize_street_name


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
            # print("Using pre-obtained OneMap API token from ONEMAP_API_TOKEN") # Reduce noise
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
            # print("OneMap API token obtained successfully")

        # Token should now be set
        if not self.token:
            raise Exception("Failed to obtain OneMap API token after refresh")

        return self.token

    def search(self, query: str, return_geom: bool = True, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Search for a location using OneMap API.

        Args:
            query: Search query (e.g., "Bishan MRT", "Block 123")
            return_geom: Whether to return geometry (lat/long)
            **kwargs: Additional parameters (e.g., pageNum)

        Returns:
            List of search results
        """
        self._get_token()

        params = {
            "searchVal": query,
            "returnGeom": "Y" if return_geom else "N",
            "getAddrDetails": "Y",
        }
        params.update(kwargs)

        try:
            response = fetch_json_with_retry(
                url=self.api_url,
                params=params,
                max_retries=2,
            )

            self.request_count += 1
            return response.get("results", [])

        except Exception:
            return []

    def geocode_address(self, address: str) -> dict[str, float] | None:
        """
        Geocode an address using OneMap API with multiple format attempts.

        Args:
            address: Full address to geocode

        Returns:
            Dictionary with latitude and longitude, or None if geocoding fails
        """
        # Try multiple address formats
        address_variants = [
            address,  # Original
            normalize_street_name(address),  # Expanded abbreviations
        ]

        # Use the search method for each variant
        for variant in address_variants:
            results = self.search(variant)
            if results:
                # Success! Return first result
                first_result = results[0]
                return {
                    "latitude": float(first_result.get("LATITUDE", 0)),
                    "longitude": float(first_result.get("LONGITUDE", 0)),
                }

        # All variants failed
        return None
