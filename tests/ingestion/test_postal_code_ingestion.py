"""Tests for HDB postal code ingestion."""

import pytest
from unittest.mock import MagicMock, patch

from resalelens.ingestion.hdb_postal_codes import ingest_hdb_postal_codes
from resalelens.models import Block


class TestPostalCodeIngestion:
    """Tests for postal code ingestion from data.gov.sg API."""

    @pytest.fixture
    def mock_api_response(self):
        """Mock data.gov.sg API response."""
        return {
            "success": True,
            "result": {
                "records": [
                    {
                        "blk_no": "514",
                        "street": "ANG MO KIO AVE 8",
                        "postal": "650514",
                    },
                    {
                        "blk_no": "123",
                        "street": "BISHAN STREET 12",
                        "postal": "570123",
                    },
                    {
                        "blk_no": "456",
                        "street": "TOA PAYOH NORTH",
                        "postal": "310456",
                    },
                ],
                "total": 3,
            },
        }

    @pytest.fixture
    def sample_blocks(self, db_session):
        """Create sample blocks for testing postal code enrichment."""
        blocks = [
            Block(
                block="514",
                street="ANG MO KIO AVENUE 8",  # Normalized
                town="ANG MO KIO",
            ),
            Block(
                block="123",
                street="BISHAN STREET 12",
                town="BISHAN",
            ),
        ]
        for block in blocks:
            db_session.add(block)
        db_session.commit()
        
        for block in blocks:
            db_session.refresh(block)
        
        yield blocks
        
        # Cleanup
        for block in blocks:
            db_session.delete(block)
        db_session.commit()

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_postal_code_ingestion_success(
        self, mock_fetch, db_session, sample_blocks, mock_api_response
    ):
        """Test successful postal code ingestion."""
        mock_fetch.return_value = mock_api_response

        summary = ingest_hdb_postal_codes(db_session)

        # Verify ingestion summary
        assert summary["total_records"] == 3
        assert summary["blocks_matched"] >= 2  # At least 2 blocks should match
        assert summary["postal_codes_added"] >= 2
        assert summary["postal_sectors_calculated"] >= 2

        # Verify blocks enriched with postal codes
        block_514 = db_session.query(Block).filter_by(block="514").first()
        assert block_514 is not None
        assert block_514.postal_code == "650514"
        assert block_514.postal_sector == "65"

        block_123 = db_session.query(Block).filter_by(block="123").first()
        assert block_123 is not None
        assert block_123.postal_code == "570123"
        assert block_123.postal_sector == "57"

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_postal_sector_extraction(
        self, mock_fetch, db_session, sample_blocks, mock_api_response
    ):
        """Test that postal sectors are correctly extracted (first 2 digits)."""
        mock_fetch.return_value = mock_api_response

        ingest_hdb_postal_codes(db_session)

        # Verify postal sectors
        block_514 = db_session.query(Block).filter_by(block="514").first()
        assert block_514.postal_sector == "65"

        block_123 = db_session.query(Block).filter_by(block="123").first()
        assert block_123.postal_sector == "57"

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_skip_existing_postal_codes(
        self, mock_fetch, db_session, sample_blocks, mock_api_response
    ):
        """Test that blocks with existing postal codes are skipped when skip_existing=True."""
        # Set postal code for one block before ingestion
        block_514 = db_session.query(Block).filter_by(block="514").first()
        block_514.postal_code = "999999"  # Wrong postal code
        db_session.commit()

        mock_fetch.return_value = mock_api_response

        summary = ingest_hdb_postal_codes(db_session, skip_existing=True)

        # Verify that block 514's postal code was not updated (existing was skipped)
        block_514_after = db_session.query(Block).filter_by(block="514").first()
        assert block_514_after.postal_code == "999999"  # Still the wrong one

        # But block 123 should be updated
        block_123 = db_session.query(Block).filter_by(block="123").first()
        assert block_123.postal_code == "570123"

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_block_not_found_handling(
        self, mock_fetch, db_session, sample_blocks, mock_api_response
    ):
        """Test handling of postal codes for blocks not in database."""
        mock_fetch.return_value = mock_api_response

        summary = ingest_hdb_postal_codes(db_session)

        # Block 456 is in API response but not in our test database
        assert summary["blocks_not_found"] >= 1

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_empty_api_response(self, mock_fetch, db_session, sample_blocks):
        """Test ingestion with empty API response."""
        mock_fetch.return_value = {
            "success": True,
            "result": {
                "records": [],
                "total": 0,
            },
        }

        summary = ingest_hdb_postal_codes(db_session)

        assert summary["total_records"] == 0
        assert summary["blocks_matched"] == 0

    @patch("resalelens.ingestion.hdb_postal_codes.fetch_json_with_retry")
    def test_batch_size_limit(
        self, mock_fetch, db_session, sample_blocks, mock_api_response
    ):
        """Test that batch_size parameter limits records processed."""
        mock_fetch.return_value = mock_api_response

        summary = ingest_hdb_postal_codes(db_session, batch_size=2)

        # Should only process first 2 records
        assert summary["total_records"] == 3  # Total fetched
        # But only 2 should be processed due to batch limit
