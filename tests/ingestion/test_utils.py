"""Unit tests for ingestion utilities."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from resalelens.ingestion.utils import (
    fetch_json_with_retry,
    log_ingestion_run,
    parse_date,
    retry_on_failure,
    validate_transaction_record,
)
from resalelens.models import IngestionStatus


class TestRetryDecorator:
    """Tests for retry_on_failure decorator."""

    def test_retry_success_on_first_attempt(self) -> None:
        """Test function succeeds on first attempt."""

        @retry_on_failure(max_retries=3)
        def succeed_immediately() -> str:
            return "success"

        result = succeed_immediately()
        assert result == "success"

    def test_retry_success_after_failures(self) -> None:
        """Test function succeeds after some failures."""
        attempts = {"count": 0}

        @retry_on_failure(max_retries=3, initial_delay=0.1)
        def succeed_on_third_attempt() -> str:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ValueError("Not yet")
            return "success"

        result = succeed_on_third_attempt()
        assert result == "success"
        assert attempts["count"] == 3

    def test_retry_exhaustion(self) -> None:
        """Test all retries are exhausted."""

        @retry_on_failure(max_retries=2, initial_delay=0.1)
        def always_fail() -> None:
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fail()


class TestLogIngestionRun:
    """Tests for log_ingestion_run context manager."""

    def test_successful_ingestion_logging(self, db_session: Session) -> None:
        """Test ingestion run is logged correctly on success."""
        with log_ingestion_run(db_session, "test_dataset") as run:
            assert run.dataset_name == "test_dataset"
            assert run.status == IngestionStatus.IN_PROGRESS
            assert run.rows_processed == 0
            run.rows_processed = 100

        # Verify status was updated to success
        db_session.refresh(run)
        assert run.status == IngestionStatus.SUCCESS
        assert run.rows_processed == 100
        assert run.completed_at is not None

    def test_failed_ingestion_logging(self, db_session: Session) -> None:
        """Test ingestion run is logged correctly on failure."""
        with pytest.raises(ValueError):
            with log_ingestion_run(db_session, "test_dataset") as run:
                run.rows_processed = 50
                raise ValueError("Test error")

        # Verify status was updated to failed
        db_session.refresh(run)
        assert run.status == IngestionStatus.FAILED
        assert run.rows_processed == 50
        assert run.error_summary == "ValueError: Test error"
        assert run.completed_at is not None


class TestFetchJsonWithRetry:
    """Tests for fetch_json_with_retry helper."""

    @patch("resalelens.ingestion.utils.httpx.Client")
    def test_successful_fetch(self, mock_client_class: MagicMock) -> None:
        """Test successful JSON fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = fetch_json_with_retry("https://example.com/api", max_retries=1)

        assert result == {"key": "value"}
        mock_client.get.assert_called_once()


class TestParseDateFunction:
    """Tests for parse_date helper."""

    def test_parse_yyyy_mm_dd(self) -> None:
        """Test parsing YYYY-MM-DD format."""
        result = parse_date("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_yyyy_mm(self) -> None:
        """Test parsing YYYY-MM format (defaults to first day)."""
        result = parse_date("2024-03")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 1

    def test_parse_dd_mm_yyyy(self) -> None:
        """Test parsing DD/MM/YYYY format."""
        result = parse_date("15/03/2024")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15

    def test_parse_invalid_format(self) -> None:
        """Test parsing invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported date format"):
            parse_date("invalid-date")


class TestValidateTransactionRecord:
    """Tests for validate_transaction_record helper."""

    def test_valid_record(self) -> None:
        """Test validation passes for complete record."""
        record = {
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
        }
        assert validate_transaction_record(record) is True

    def test_missing_required_field(self) -> None:
        """Test validation fails when required field is missing."""
        record = {
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
        }
        assert validate_transaction_record(record) is False

    def test_empty_field_value(self) -> None:
        """Test validation fails when field has empty value."""
        record = {
            "month": "2024-01",
            "block": "",  # Empty value
            "street_name": "Test Street",
            "flat_type": "3 ROOM",
            "storey_range": "01 TO 03",
            "floor_area_sqm": "75.5",
            "resale_price": "350000",
            "lease_commence_date": "1985",
            "town": "Test Town",
            "flat_model": "Improved",
        }
        assert validate_transaction_record(record) is False
