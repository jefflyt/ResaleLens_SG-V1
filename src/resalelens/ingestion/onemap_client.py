"""OneMap API Client for POI data fetching."""

import time
from typing import Any

import httpx


class OneMapClient:
    """Client for interacting with OneMap API (Public Search)."""

    BASE_URL = "https://www.onemap.gov.sg/api/common/elastic/search"

    def fetch_poi_search(self, search_term: str) -> list[dict[str, Any]]:
        """
        Fetch POI data by searching through OneMap.
        Handles pagination automatically.

        Args:
            search_term: Search query (e.g. 'MRT Station', 'Supermarket')

        Returns:
            List of POI records
        """
        results = []
        page = 1

        while True:
            params = {
                "searchVal": search_term,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": page,
            }

            try:
                with httpx.Client() as client:
                    response = client.get(self.BASE_URL, params=params)
                    response.raise_for_status()
                    data = response.json()

                    found = data.get("results", [])
                    if not found:
                        break

                    results.extend(found)

                    # OneMap pagination logic: check total pages
                    total_pages = data.get("totalNumPages", 0)
                    if page >= total_pages:
                        break

                    page += 1
                    time.sleep(0.2)  # Politeness

            except Exception as e:
                print(f"Search failed for '{search_term}' page {page}: {e}")
                break

        return results
