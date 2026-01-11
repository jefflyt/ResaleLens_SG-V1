"""Unit tests for HDB blocks ingestion."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from resalelens.ingestion.hdb_blocks import OneMapClient, ingest_hdb_blocks
from resalelens.models import Block, IngestionRun, IngestionStatus, Transaction


class TestOneMapClient:
    """Tests for OneMap geocoding client."""

    @patch.dict(
        os.environ,
        {"ONEMAP_EMAIL": "test@example.com", "ONEMAP_PASSWORD": "testpass"},
        clear=False,  # Don't clear other env vars
    )
    @patch.dict(os.environ, {"ONEMAP_API_TOKEN": ""}, clear=False)  # Clear token to test email/password flow
    @patch("resalelens.ingestion.hdb_blocks.fetch_json_with_retry")
    def test_get_token(self, mock_fetch: MagicMock) -> None:
        """Test getting OneMap API token via email/password."""
        mock_fetch.return_value = {"access_token": "test-token-123"}

        client = OneMapClient()
        token = client._get_token()

        assert token == "test-token-123"
        assert client.request_count == 0

    @patch.dict(
        os.environ,
        {"ONEMAP_EMAIL": "test@example.com", "ONEMAP_PASSWORD": "testpass"},
        clear=False,
    )
    @patch.dict(os.environ, {"ONEMAP_API_TOKEN": ""}, clear=False)  # Clear token to test email/password flow
    @patch("resalelens.ingestion.hdb_blocks.fetch_json_with_retry")
    def test_geocode_address_success(self, mock_fetch: MagicMock) -> None:
        """Test successful address geocoding via email/password auth."""
        # Mock token response and geocoding response
        mock_fetch.side_effect = [
            {"access_token": "test-token-123"},  # Token fetch
            {
                "results": [
                    {"LATITUDE": "1.3521", "LONGITUDE": "103.8198"},
                ]
            },  # Geocoding result
        ]

        client = OneMapClient()
        result = client.geocode_address("123 Test Street, Singapore")

        assert result is not None
        assert result["latitude"] == 1.3521
        assert result["longitude"] == 103.8198

    @patch.dict(
        os.environ,
        {"ONEMAP_EMAIL": "test@example.com", "ONEMAP_PASSWORD": "testpass"},
    )
    @patch("resalelens.ingestion.hdb_blocks.fetch_json_with_retry")
    def test_geocode_address_no_results(self, mock_fetch: MagicMock) -> None:
        """Test geocoding with no results."""
        # Mock token response and empty results
        mock_fetch.side_effect = [
            {"access_token": "test-token-123"},
            {"results": []},
        ]

        client = OneMapClient()
        result = client.geocode_address("Invalid Address")

        assert result is None


class TestHDBBlocksIngestion:
    """Tests for HDB blocks ingestion."""

    @patch.dict(
        os.environ,
        {"ONEMAP_EMAIL": "test@example.com", "ONEMAP_PASSWORD": "testpass"},
    )
    @patch("resalelens.ingestion.hdb_blocks.OneMapClient.geocode_address")
    @patch("resalelens.ingestion.hdb_blocks.OneMapClient._get_token")
    def test_successful_ingestion(
        self, mock_get_token: MagicMock, mock_geocode: MagicMock, db_session: Session
    ) -> None:
        """Test successful ingestion of blocks."""
        # Create sample transactions to extract blocks from
        run = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
            rows_processed=0,
        )
        db_session.add(run)
        db_session.commit()

        transaction1 = Transaction(
            date=datetime.strptime("2024-01", "%Y-%m").date(),
            block="123",
            street="Test Street",
            flat_type="3 ROOM",
            storey_range="01 TO 03",
            floor_area_sqm=75.5,
            price=350000,
            lease_commence_date=1985,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=run.id,
        )
        transaction2 = Transaction(
            date=datetime.strptime("2024-02", "%Y-%m").date(),
            block="456",
            street="Another Street",
            flat_type="4 ROOM",
            storey_range="04 TO 06",
            floor_area_sqm=95.0,
            price=450000,
            lease_commence_date=1990,
            town="Another Town",
            flat_model="New Generation",
            ingestion_run_id=run.id,
        )
        db_session.add_all([transaction1, transaction2])
        db_session.commit()

        # Mock geocoding results
        mock_get_token.return_value = "test-token"
        mock_geocode.side_effect = [
            {"latitude": 1.3521, "longitude": 103.8198},
            {"latitude": 1.3525, "longitude": 103.8205},
        ]

        summary = ingest_hdb_blocks(db_session)

        # Verify summary
        assert summary["total_blocks"] == 2
        assert summary["inserted"] == 2
        assert summary["geocoded"] == 2
        assert summary["geocoding_failed"] == 0

        # Verify blocks were inserted
        blocks = db_session.query(Block).all()
        assert len(blocks) == 2
        assert blocks[0].block == "123"
        assert float(blocks[0].latitude) == 1.3521
        assert blocks[1].block == "456"
        assert float(blocks[1].latitude) == 1.3525

    @patch.dict(
        os.environ,
        {"ONEMAP_EMAIL": "test@example.com", "ONEMAP_PASSWORD": "testpass"},
    )
    @patch("resalelens.ingestion.hdb_blocks.OneMapClient.geocode_address")
    @patch("resalelens.ingestion.hdb_blocks.OneMapClient._get_token")
    def test_geocoding_failure_handling(
        self, mock_get_token: MagicMock, mock_geocode: MagicMock, db_session: Session
    ) -> None:
        """Test handling of geocoding failures."""
        # Create sample transaction
        run = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
            rows_processed=0,
        )
        db_session.add(run)
        db_session.commit()

        transaction = Transaction(
            date=datetime.strptime("2024-01", "%Y-%m").date(),
            block="123",
            street="Test Street",
            flat_type="3 ROOM",
            storey_range="01 TO 03",
            floor_area_sqm=75.5,
            price=350000,
            lease_commence_date=1985,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=run.id,
        )
        db_session.add(transaction)
        db_session.commit()

        # Mock geocoding failure
        mock_get_token.return_value = "test-token"
        mock_geocode.return_value = None  # Geocoding failed

        summary = ingest_hdb_blocks(db_session)

        # Verify summary
        assert summary["total_blocks"] == 1
        assert summary["inserted"] == 1
        assert summary["geocoded"] == 0
        assert summary["geocoding_failed"] == 1

        # Verify block was still inserted with null coordinates
        block = db_session.query(Block).first()
        assert block is not None
        assert block.block == "123"
        assert block.latitude is None
        assert block.longitude is None
