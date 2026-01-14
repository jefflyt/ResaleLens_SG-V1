"""Unit tests for HDB transactions ingestion."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from resalelens.ingestion.hdb_transactions import ingest_hdb_transactions
from resalelens.models import IngestionRun, IngestionStatus, Transaction


class TestHDBTransactionsIngestion:
    """Tests for HDB transactions ingestion."""

    @patch.dict(
        os.environ,
        {
            "DATA_GOV_SG_API_URL": "https://test-api.gov.sg",
            "DATA_GOV_SG_RESOURCE_ID": "test-resource-id",
        },
    )
    @patch("resalelens.ingestion.hdb_transactions.fetch_json_with_retry")
    def test_successful_ingestion(self, mock_fetch: MagicMock, db_session: Session) -> None:
        """Test successful ingestion of transactions."""
        # Mock API response
        mock_fetch.return_value = {
            "result": {
                "total": 2,
                "records": [
                    {
                        "month": "2024-01",
                        "block": "123",
                        "street_name": "Test Street",
                        "flat_type": "3 ROOM",
                        "storey_range": "01 TO 03",
                        "floor_area_sqm": "75.5",
                        "resale_price": "350000",
                        "lease_commence_date": "1985",
                        "town": "Test Town",
                        "flat_model": "Improved",
                    },
                    {
                        "month": "2024-02",
                        "block": "456",
                        "street_name": "Another Street",
                        "flat_type": "4 ROOM",
                        "storey_range": "04 TO 06",
                        "floor_area_sqm": "95.0",
                        "resale_price": "450000",
                        "lease_commence_date": "1990",
                        "town": "Another Town",
                        "flat_model": "New Generation",
                    },
                ],
            }
        }

        summary = ingest_hdb_transactions(db_session)

        # Verify summary
        assert summary["total_fetched"] == 2
        assert summary["inserted"] == 2
        assert summary["updated"] == 0
        assert summary["skipped"] == 0
        assert summary["errors"] == 0

        # Verify transactions were inserted
        transactions = db_session.query(Transaction).all()
        assert len(transactions) == 2
        assert transactions[0].block == "123"
        assert transactions[1].block == "456"

        # Verify ingestion run was logged
        run = db_session.query(IngestionRun).first()
        assert run is not None
        assert run.dataset_name == "hdb_transactions"
        assert run.status == IngestionStatus.SUCCESS
        assert run.rows_processed == 2

    @patch.dict(
        os.environ,
        {
            "DATA_GOV_SG_API_URL": "https://test-api.gov.sg",
            "DATA_GOV_SG_RESOURCE_ID": "test-resource-id",
        },
    )
    @patch("resalelens.ingestion.hdb_transactions.fetch_json_with_retry")
    def test_update_existing_transaction(self, mock_fetch: MagicMock, db_session: Session) -> None:
        """Test updating existing transaction."""
        # Create a block first to satisfy foreign key constraint
        from resalelens.models import Block

        block = Block(
            block="123",
            street="Test Street",
            town="Test Town",
        )
        db_session.add(block)
        db_session.commit()

        # Create ingestion run first (needed for foreign key)
        run = IngestionRun(
            id=1,
            dataset_name="hdb_transactions",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
            rows_processed=0,
        )
        db_session.add(run)
        db_session.commit()

        # Create existing transaction
        existing = Transaction(
            date=datetime.strptime("2024-01", "%Y-%m").date(),
            block="123",
            street="Test Street",
            flat_type="3 ROOM",
            storey_range="01 TO 03",
            floor_area_sqm=75.5,
            price=340000,  # Old price
            lease_commence_date=1985,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=1,
            block_id=block.id,  # Link to block
        )
        db_session.add(existing)
        db_session.commit()

        # Mock API response with updated price
        mock_fetch.return_value = {
            "result": {
                "total": 1,
                "records": [
                    {
                        "month": "2024-01",
                        "block": "123",
                        "street_name": "Test Street",
                        "flat_type": "3 ROOM",
                        "storey_range": "01 TO 03",
                        "floor_area_sqm": "75.5",
                        "resale_price": "350000",  # Updated price
                        "lease_commence_date": "1985",
                        "town": "Test Town",
                        "flat_model": "Improved",
                    }
                ],
            }
        }

        summary = ingest_hdb_transactions(db_session)

        # With bulk upsert, we can't distinguish updates from inserts
        # The count goes into "inserted" regardless
        assert summary["total_fetched"] == 1
        assert summary["inserted"] == 1  # Bulk upsert counts all as "inserted"

        # Verify transaction was updated (price changed)
        updated = db_session.query(Transaction).filter_by(block="123").first()
        assert updated is not None
        assert updated.price == 350000  # Price was updated

    @patch.dict(
        os.environ,
        {
            "DATA_GOV_SG_API_URL": "https://test-api.gov.sg",
            "DATA_GOV_SG_RESOURCE_ID": "test-resource-id",
        },
    )
    @patch("resalelens.ingestion.hdb_transactions.fetch_json_with_retry")
    def test_skip_invalid_records(self, mock_fetch: MagicMock, db_session: Session) -> None:
        """Test skipping invalid records."""
        # Mock API response with one valid and one invalid record
        mock_fetch.return_value = {
            "result": {
                "total": 2,
                "records": [
                    {
                        "month": "2024-01",
                        "block": "123",
                        # Missing street_name
                        "flat_type": "3 ROOM",
                        "storey_range": "01 TO 03",
                        "floor_area_sqm": "75.5",
                        "resale_price": "350000",
                        "lease_commence_date": "1985",
                        "town": "Test Town",
                        "flat_model": "Improved",
                    },
                    {
                        "month": "2024-02",
                        "block": "456",
                        "street_name": "Another Street",
                        "flat_type": "4 ROOM",
                        "storey_range": "04 TO 06",
                        "floor_area_sqm": "95.0",
                        "resale_price": "450000",
                        "lease_commence_date": "1990",
                        "town": "Another Town",
                        "flat_model": "New Generation",
                    },
                ],
            }
        }

        summary = ingest_hdb_transactions(db_session)

        # Verify summary
        assert summary["total_fetched"] == 2
        assert summary["inserted"] == 1
        assert summary["skipped"] == 1

    def test_missing_resource_id(self, db_session: Session) -> None:
        """Test error when DATA_GOV_SG_RESOURCE_ID is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DATA_GOV_SG_RESOURCE_ID"):
                ingest_hdb_transactions(db_session)
