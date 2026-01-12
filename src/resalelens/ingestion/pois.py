"""POI ingestion from OneMap API."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..api.onemap import OneMapClient
from ..models import POI, POIType
from .utils import log_ingestion_run


def ingest_pois(session: Session) -> dict[str, int]:
    """
    Ingest Points of Interest (POIs) from OneMap.

    Categories:
    - Transport: MRT, LRT
    - Education: Primary Schools, Secondary Schools
    - Amenities: Supermarkets (NTUC, Sheng Siong, Cold Storage, Giant, Prime, Don Don Donki, etc.)
    - Food: Hawker Centres, Food Centres, Markets
    - Shopping: Malls, Shopping Centres, Plazas
    - Healthcare: Clinics, Polyclinics
    - Recreation: Parks, Park Connectors

    Args:
        session: Database session

    Returns:
        Summary of ingestion
    """
    client = OneMapClient()

    summary = {
        "total_found": 0,
        "inserted": 0,
        "duplicates": 0,
        "errors": 0,
    }

    # Define categories to search
    categories = [
        # Transport
        {"query": "MRT STATION", "type": POIType.MRT},
        {"query": "LRT STATION", "type": POIType.LRT},

        # Education
        {"query": "PRIMARY SCHOOL", "type": POIType.SCHOOL},
        {"query": "SECONDARY SCHOOL", "type": POIType.SCHOOL},

        # Supermarkets - Major chains
        {"query": "NTUC", "type": POIType.SUPERMARKET},
        {"query": "FAIRPRICE", "type": POIType.SUPERMARKET},
        {"query": "SHENG SIONG", "type": POIType.SUPERMARKET},
        {"query": "COLD STORAGE", "type": POIType.SUPERMARKET},
        {"query": "GIANT", "type": POIType.SUPERMARKET},
        {"query": "PRIME SUPERMARKET", "type": POIType.SUPERMARKET},
        {"query": "DON DON DONKI", "type": POIType.SUPERMARKET},
        {"query": "U STARS", "type": POIType.SUPERMARKET},
        {"query": "MARKETPLACE", "type": POIType.SUPERMARKET},

        # Hawker Centres & Food Courts
        {"query": "HAWKER CENTRE", "type": POIType.HAWKER},
        {"query": "FOOD CENTRE", "type": POIType.HAWKER},
        {"query": "MARKET AND FOOD CENTRE", "type": POIType.HAWKER},
        {"query": "MARKET & FOOD CENTRE", "type": POIType.HAWKER},

        # Shopping Malls - Broader terms
        {"query": "SHOPPING CENTRE", "type": POIType.MALL},
        {"query": "PLAZA", "type": POIType.MALL},
        {"query": "MALL", "type": POIType.MALL},

        # Clinics
        {"query": "CLINIC", "type": POIType.CLINIC},
        {"query": "POLYCLINIC", "type": POIType.CLINIC},

        # Parks - Specific to avoid noise
        {"query": "PARK CONNECTOR", "type": POIType.PARK},
        {"query": "NEIGHBOURHOOD PARK", "type": POIType.PARK},
    ]

    with log_ingestion_run(session, "onemap_pois") as run:
        print("Starting POI ingestion...")

        for category in categories:
            query = category["query"]
            poi_type = category["type"]
            print(f"Searching for {query} ({poi_type.value})...")

            page = 1
            total_category_found = 0

            while True:
                try:
                    results = client.search(query, return_geom=True, pageNum=page)
                    if not results:
                        break

                    batch_count = len(results)
                    total_category_found += batch_count
                    summary["total_found"] += batch_count

                    for result in results:
                        name = result.get("SEARCHVAL", "").strip()
                        lat_str = result.get("LATITUDE")
                        lon_str = result.get("LONGITUDE")

                        if not name or not lat_str or not lon_str:
                            continue

                        try:
                            lat = float(lat_str)
                            lon = float(lon_str)
                        except ValueError:
                            continue

                        # Check for existence
                        existing = session.query(POI).filter(
                            POI.name == name,
                            POI.poi_type == poi_type
                        ).first()

                        if existing:
                            summary["duplicates"] += 1
                            continue

                        # Create new POI
                        poi = POI(
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            poi_type=poi_type,
                        )
                        session.add(poi)
                        summary["inserted"] += 1

                    # Commit batch
                    session.commit()

                    # Log progress every few pages or just at end?
                    # OneMap is slow, 10 items per page.
                    # e.g. 15 pages for MRTs.
                    print(f"  Page {page}: Found {batch_count} items")

                    page += 1

                except Exception as e:
                    print(f"Error processing page {page} for {query}: {e}")
                    summary["errors"] += 1
                    break

            print(f"Category complete: Found {total_category_found} total for {query}")


        run.rows_processed = summary["inserted"]
        print(f"POI Ingestion Complete: {summary}")

    return summary
