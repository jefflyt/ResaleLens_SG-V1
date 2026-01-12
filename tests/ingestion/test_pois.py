"""Unit tests for POI ingestion from OneMap API."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from resalelens.ingestion.pois import ingest_pois
from resalelens.models import POI, POIType


@pytest.fixture
def mock_onemap_client():
    """Mock OneMap client for testing."""
    with patch("resalelens.ingestion.pois.OneMapClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


def test_ingest_pois_success(db_session: Session, mock_onemap_client: MagicMock):
    """Test successful POI ingestion with mocked OneMap responses."""
    # Mock OneMap search results
    mock_onemap_client.search.side_effect = [
        # MRT stations
        [
            {
                "SEARCHVAL": "ANG MO KIO MRT STATION",
                "LATITUDE": "1.369995",
                "LONGITUDE": "103.849549",
            },
            {
                "SEARCHVAL": "BISHAN MRT STATION",
                "LATITUDE": "1.351236",
                "LONGITUDE": "103.848456",
            },
        ],
        [],  # End of MRT pagination
        # LRT stations
        [
            {
                "SEARCHVAL": "BUKIT PANJANG LRT STATION",
                "LATITUDE": "1.378413",
                "LONGITUDE": "103.761787",
            },
        ],
        [],  # End of LRT pagination
        # Schools
        [
            {
                "SEARCHVAL": "ANG MO KIO PRIMARY SCHOOL",
                "LATITUDE": "1.374025",
                "LONGITUDE": "103.839486",
            },
        ],
        [],
        # Supermarkets
        [
            {
                "SEARCHVAL": "NTUC FAIRPRICE",
                "LATITUDE": "1.370000",
                "LONGITUDE": "103.850000",
            },
        ],
        [],
        # Continue with empty results for remaining categories
        *[[] for _ in range(40)],  # Remaining categories return empty
    ]

    # Run ingestion
    summary = ingest_pois(db_session)

    # Verify summary
    assert summary["total_found"] == 5
    assert summary["inserted"] == 5
    assert summary["duplicates"] == 0
    assert summary["errors"] == 0

    # Verify database records
    all_pois = db_session.query(POI).all()
    assert len(all_pois) == 5

    # Verify MRT stations
    mrt_pois = db_session.query(POI).filter(POI.poi_type == POIType.MRT).all()
    assert len(mrt_pois) == 2
    assert any(poi.name == "ANG MO KIO MRT STATION" for poi in mrt_pois)
    assert any(poi.name == "BISHAN MRT STATION" for poi in mrt_pois)

    # Verify LRT stations
    lrt_pois = db_session.query(POI).filter(POI.poi_type == POIType.LRT).all()
    assert len(lrt_pois) == 1
    assert lrt_pois[0].name == "BUKIT PANJANG LRT STATION"


def test_ingest_pois_deduplication(db_session: Session, mock_onemap_client: MagicMock):
    """Test that duplicate POIs are not inserted."""
    # Insert existing POI
    existing_poi = POI(
        name="ANG MO KIO MRT STATION",
        latitude=1.369995,
        longitude=103.849549,
        poi_type=POIType.MRT,
    )
    db_session.add(existing_poi)
    db_session.commit()

    # Mock OneMap to return the same POI
    mock_onemap_client.search.side_effect = [
        [
            {
                "SEARCHVAL": "ANG MO KIO MRT STATION",
                "LATITUDE": "1.369995",
                "LONGITUDE": "103.849549",
            },
        ],
        [],  # End of pagination
        *[[] for _ in range(50)],  # Empty results for other categories
    ]

    # Run ingestion
    summary = ingest_pois(db_session)

    # Verify duplicate was detected
    assert summary["total_found"] == 1
    assert summary["inserted"] == 0
    assert summary["duplicates"] == 1

    # Verify only one POI exists in database
    all_pois = db_session.query(POI).all()
    assert len(all_pois) == 1


def test_ingest_pois_missing_fields(db_session: Session, mock_onemap_client: MagicMock):
    """Test that POIs with missing required fields are skipped."""
    # Mock OneMap with incomplete data
    mock_onemap_client.search.side_effect = [
        [
            # Missing name
            {
                "SEARCHVAL": "",
                "LATITUDE": "1.369995",
                "LONGITUDE": "103.849549",
            },
            # Missing latitude
            {
                "SEARCHVAL": "SOME MRT STATION",
                "LATITUDE": None,
                "LONGITUDE": "103.849549",
            },
            # Valid POI
            {
                "SEARCHVAL": "VALID MRT STATION",
                "LATITUDE": "1.369995",
                "LONGITUDE": "103.849549",
            },
        ],
        [],
        *[[] for _ in range(50)],
    ]

    # Run ingestion
    summary = ingest_pois(db_session)

    # Verify only valid POI was inserted
    assert summary["inserted"] == 1
    all_pois = db_session.query(POI).all()
    assert len(all_pois) == 1
    assert all_pois[0].name == "VALID MRT STATION"


def test_ingest_pois_invalid_coordinates(db_session: Session, mock_onemap_client: MagicMock):
    """Test that POIs with invalid coordinate formats are skipped."""
    # Mock OneMap with invalid coordinate data
    mock_onemap_client.search.side_effect = [
        [
            # Invalid latitude format
            {
                "SEARCHVAL": "INVALID COORDS MRT",
                "LATITUDE": "not_a_number",
                "LONGITUDE": "103.849549",
            },
            # Valid POI
            {
                "SEARCHVAL": "VALID MRT STATION",
                "LATITUDE": "1.369995",
                "LONGITUDE": "103.849549",
            },
        ],
        [],
        *[[] for _ in range(50)],
    ]

    # Run ingestion
    summary = ingest_pois(db_session)

    # Verify only valid POI was inserted
    assert summary["inserted"] == 1
    all_pois = db_session.query(POI).all()
    assert len(all_pois) == 1
    assert all_pois[0].name == "VALID MRT STATION"


def test_ingest_pois_api_error(db_session: Session, mock_onemap_client: MagicMock):
    """Test error handling when OneMap API fails."""
    # Mock OneMap to raise an exception
    mock_onemap_client.search.side_effect = Exception("API connection failed")

    # Run ingestion - should not crash
    summary = ingest_pois(db_session)

    # Verify error was logged
    assert summary["errors"] > 0
    assert summary["inserted"] == 0


def test_ingest_pois_multiple_categories(db_session: Session, mock_onemap_client: MagicMock):
    """Test ingestion across multiple POI categories."""
    # Mock different POI types
    mock_onemap_client.search.side_effect = [
        # MRT
        [{"SEARCHVAL": "TEST MRT", "LATITUDE": "1.3", "LONGITUDE": "103.8"}],
        [],
        # LRT
        [{"SEARCHVAL": "TEST LRT", "LATITUDE": "1.4", "LONGITUDE": "103.9"}],
        [],
        # Schools
        [{"SEARCHVAL": "TEST SCHOOL", "LATITUDE": "1.5", "LONGITUDE": "104.0"}],
        [],
        [{"SEARCHVAL": "TEST SCHOOL 2", "LATITUDE": "1.6", "LONGITUDE": "104.1"}],
        [],
        # Supermarkets
        [{"SEARCHVAL": "TEST NTUC", "LATITUDE": "1.7", "LONGITUDE": "104.2"}],
        [],
        # Empty for remaining
        *[[] for _ in range(50)],
    ]

    # Run ingestion
    summary = ingest_pois(db_session)

    # Verify all categories were processed
    assert summary["inserted"] == 5

    # Verify different POI types
    assert db_session.query(POI).filter(POI.poi_type == POIType.MRT).count() == 1
    assert db_session.query(POI).filter(POI.poi_type == POIType.LRT).count() == 1
    assert db_session.query(POI).filter(POI.poi_type == POIType.SCHOOL).count() == 2
    assert db_session.query(POI).filter(POI.poi_type == POIType.SUPERMARKET).count() == 1
