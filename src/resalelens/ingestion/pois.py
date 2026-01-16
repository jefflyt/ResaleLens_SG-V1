"""[DEPRECATED] POI ingestion from OneMap API - use alternative data source."""

from __future__ import annotations

from sqlalchemy.orm import Session


def ingest_pois(session: Session) -> dict[str, int]:
    """
    [DEPRECATED] Ingest Points of Interest (POIs) from OneMap.

    This function has been deprecated because the OneMap API client
    was removed. Use an alternative data source for POI ingestion.

    Categories that were supported:
    - Transport: MRT, LRT
    - Education: Primary Schools, Secondary Schools
    - Amenities: Supermarkets
    - Food: Hawker Centres, Food Centres, Markets
    - Shopping: Malls, Shopping Centres, Plazas
    - Healthcare: Clinics, Polyclinics
    - Recreation: Parks, Park Connectors

    Args:
        session: Database session

    Returns:
        Summary of ingestion

    Raises:
        NotImplementedError: This function is deprecated
    """
    raise NotImplementedError(
        "ingest_pois() is deprecated. OneMap API client has been removed. "
        "Use an alternative data source for POI ingestion."
    )

