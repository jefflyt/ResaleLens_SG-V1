"""Tests for incremental sync functionality."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from resalelens.ingestion.hdb_transactions import ingest_hdb_transactions
from resalelens.models import IngestionRun, IngestionStatus, Transaction


class TestIncrementalSync:
    """Tests for incremental ingestion mode."""

    def test_incremental_sync_with_existing_data(self, db_session: Session, monkeypatch):
        """Test incremental sync skips old records when data exists."""
        # Create dependencies first
        from resalelens.models import Block

        run = IngestionRun(id=1, dataset_name="hdb_transactions", started_at=datetime.utcnow(), status=IngestionStatus.SUCCESS, rows_processed=0)
        db_session.add(run)
        block = Block(block="123", street="Test Street", town="Test Town")
        db_session.add(block)
        db_session.commit()

        # Create existing transaction with date 2024-01-01
        existing_txn = Transaction(
            date=date(2024, 1, 1),
            block="123",
            street="Test Street",
            flat_type="4 ROOM",
            storey_range="01 TO 03",
            floor_area_sqm=90.0,
            price=400000,
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=1,
            block_id=block.id,
        )
        db_session.add(existing_txn)
        db_session.commit()

        # Mock API response with mix of old and new records
        def mock_fetch(url, params, max_retries=3):
            return {
                "result": {
                    "records": [
                        {
                            "month": "2023-12",  # Older than existing
                            "block": "100",
                            "street_name": "Old Street",
                            "flat_type": "3 ROOM",
                            "storey_range": "01 TO 03",
                            "floor_area_sqm": "70.0",
                            "resale_price": "300000",
                            "lease_commence_date": "1985",
                            "town": "Old Town",
                            "flat_model": "Standard",
                        },
                        {
                            "month": "2024-02",  # Newer than existing
                            "block": "456",
                            "street_name": "New Street",
                            "flat_type": "5 ROOM",
                            "storey_range": "10 TO 12",
                            "floor_area_sqm": "110.0",
                            "resale_price": "600000",
                            "lease_commence_date": "2000",
                            "town": "New Town",
                            "flat_model": "Premium",
                        },
                    ],
                    "total": 2,
                }
            }

        monkeypatch.setattr(
            "resalelens.ingestion.hdb_transactions.fetch_json_with_retry", mock_fetch
        )

        # Run incremental sync
        summary = ingest_hdb_transactions(db_session, incremental=True)

        # Verify only new record was processed
        assert summary["incremental"] is True
        assert summary["since_date"] == "2024-01-01"
        assert summary["skipped"] >= 1  # Old record skipped
        assert summary["inserted"] >= 1  # New record inserted

    def test_incremental_sync_falls_back_to_full_refresh(self, db_session: Session, monkeypatch):
        """Test incremental sync falls back to full refresh when no data exists."""
        # No existing data in database

        def mock_fetch(url, params, max_retries=3):
            return {
                "result": {
                    "records": [
                        {
                            "month": "2024-01",
                            "block": "123",
                            "street_name": "Test Street",
                            "flat_type": "4 ROOM",
                            "storey_range": "01 TO 03",
                            "floor_area_sqm": "90.0",
                            "resale_price": "400000",
                            "lease_commence_date": "1990",
                            "town": "Test Town",
                            "flat_model": "Improved",
                        }
                    ],
                    "total": 1,
                }
            }

        monkeypatch.setattr(
            "resalelens.ingestion.hdb_transactions.fetch_json_with_retry", mock_fetch
        )

        # Run incremental sync
        summary = ingest_hdb_transactions(db_session, incremental=True)

        # Verify it fell back to full refresh
        assert summary["incremental"] is False  # Fell back
        assert summary["since_date"] is None
        assert summary["inserted"] >= 1

    def test_full_refresh_mode(self, db_session: Session, monkeypatch):
        """Test full refresh mode processes all records regardless of date."""
        # Create dependencies first
        from resalelens.models import Block

        run = IngestionRun(id=1, dataset_name="hdb_transactions", started_at=datetime.utcnow(), status=IngestionStatus.SUCCESS, rows_processed=0)
        db_session.add(run)
        block = Block(block="123", street="Test Street", town="Test Town")
        db_session.add(block)
        db_session.commit()

        # Create existing transaction
        existing_txn = Transaction(
            date=date(2024, 1, 1),
            block="123",
            street="Test Street",
            flat_type="4 ROOM",
            storey_range="01 TO 03",
            floor_area_sqm=90.0,
            price=400000,
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=1,
            block_id=block.id,
        )
        db_session.add(existing_txn)
        db_session.commit()

        def mock_fetch(url, params, max_retries=3):
            return {
                "result": {
                    "records": [
                        {
                            "month": "2023-12",  # Older than existing
                            "block": "100",
                            "street_name": "Old Street",
                            "flat_type": "3 ROOM",
                            "storey_range": "01 TO 03",
                            "floor_area_sqm": "70.0",
                            "resale_price": "300000",
                            "lease_commence_date": "1985",
                            "town": "Old Town",
                            "flat_model": "Standard",
                        }
                    ],
                    "total": 1,
                }
            }

        monkeypatch.setattr(
            "resalelens.ingestion.hdb_transactions.fetch_json_with_retry", mock_fetch
        )

        # Run full refresh (incremental=False)
        summary = ingest_hdb_transactions(db_session, incremental=False)

        # Verify all records processed (not skipped by date)
        assert summary["incremental"] is False
        assert summary["since_date"] is None
        assert summary["inserted"] >= 1  # Old record still processed
