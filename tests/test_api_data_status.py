"""Integration tests for Data Status API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from resalelens.models import IngestionRun, IngestionStatus


class TestDataStatusAPI:
    """Tests for Data Status page and API endpoints."""

    @pytest.fixture
    def sample_data_status_runs(self, db_session):
        """Create sample ingestion runs for data status tests."""
        now = datetime.now(timezone.utc)

        runs = [
            # Healthy: Recent successful run (12 hours ago)
            IngestionRun(
                dataset_name="hdb_transactions",
                started_at=now - timedelta(hours=12),
                completed_at=now - timedelta(hours=12),
                status=IngestionStatus.SUCCESS,
                rows_processed=1000,
            ),
            # Healthy: Recent successful run for blocks (1 day ago)
            IngestionRun(
                dataset_name="hdb_blocks",
                started_at=now - timedelta(days=1),
                completed_at=now - timedelta(days=1),
                status=IngestionStatus.SUCCESS,
                rows_processed=500,
            ),
            # Delayed: Old successful run for POIs (35 days ago - exceeds 30-day threshold)
            IngestionRun(
                dataset_name="pois",
                started_at=now - timedelta(days=35),
                completed_at=now - timedelta(days=35),
                status=IngestionStatus.SUCCESS,
                rows_processed=200,
            ),
        ]

        for run in runs:
            db_session.add(run)

        db_session.commit()
        yield runs

        # Cleanup
        for run in runs:
            db_session.delete(run)
        db_session.commit()

    def test_data_status_page_renders(self, client: TestClient, sample_data_status_runs):
        """Test GET /data-status returns 200 and renders HTML."""
        response = client.get("/api/data-status")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"].lower()
        
        # Check for key elements in HTML
        assert "Data Status" in response.text
        assert "hdb_transactions" in response.text
        assert "hdb_blocks" in response.text

    def test_data_status_json_api(self, client: TestClient, sample_data_status_runs):
        """Test GET /api/data-status returns correct JSON schema."""
        response = client.get("/api/api/data-status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "datasets" in data
        assert isinstance(data["datasets"], list)
        assert len(data["datasets"]) == 5  # All 5 tracked datasets

        # Verify dataset schema
        for dataset in data["datasets"]:
            assert "dataset_name" in dataset
            assert "source" in dataset
            assert "next_ingest" in dataset
            assert "status" in dataset
            assert "status_label" in dataset
            # last_ingest can be None for never-run datasets
            assert "last_ingest" in dataset

    def test_data_status_shows_delayed_badge(self, client: TestClient, db_session):
        """Verify 'delayed' banner and badge appear when dataset is stale."""
        # Create delayed transaction run (>48h old)
        now = datetime.now(timezone.utc)
        old_run = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(old_run)
        db_session.commit()

        response = client.get("/api/data-status")

        assert response.status_code == 200
        # Check for delayed banner
        assert "Data Delayed" in response.text or "delayed" in response.text.lower()

        # Cleanup
        db_session.delete(old_run)
        db_session.commit()

    def test_data_status_empty_state(self, client: TestClient):
        """Test Data Status page when no ingestion runs exist."""
        # Don't create any runs - table is empty

        response = client.get("/api/data-status")

        assert response.status_code == 200
        # Should still render page, showing "never run" status
        assert "Data Status" in response.text
        # All datasets should show "Never Run" or similar
        assert "Never" in response.text or "never" in response.text.lower()

    def test_data_status_json_response_structure(self, client: TestClient, sample_data_status_runs):
        """Test JSON API response has correct structure for all datasets."""
        response = client.get("/api/api/data-status")

        assert response.status_code == 200
        data = response.json()

        datasets = data["datasets"]

        # Verify all tracked datasets are present
        dataset_names = [d["dataset_name"] for d in datasets]
        assert "hdb_transactions" in dataset_names
        assert "hdb_blocks" in dataset_names
        assert "hdb_property_info" in dataset_names
        assert "pois" in dataset_names
        assert "block_pois" in dataset_names

        # Verify status values are valid
        valid_statuses = {"healthy", "delayed", "failed", "never_run", "in_progress"}
        for dataset in datasets:
            assert dataset["status"] in valid_statuses

    def test_data_status_shows_healthy_status(self, client: TestClient, sample_data_status_runs):
        """Verify healthy datasets show green badge."""
        response = client.get("/api/data-status")

        assert response.status_code == 200
        # Check for healthy badge class
        assert "badge-healthy" in response.text or "Healthy" in response.text

    def test_data_status_failed_run(self, client: TestClient, db_session):
        """Test that failed ingestion runs show 'Failed' status."""
        now = datetime.now(timezone.utc)
        failed_run = IngestionRun(
            dataset_name="hdb_blocks",
            started_at=now - timedelta(hours=1),
            completed_at=None,
            status=IngestionStatus.FAILED,
            rows_processed=0,
            error_summary="Connection timeout",
        )
        db_session.add(failed_run)
        db_session.commit()

        response = client.get("/api/api/data-status")

        assert response.status_code == 200
        data = response.json()

        # Find blocks dataset
        blocks_dataset = next(d for d in data["datasets"] if d["dataset_name"] == "hdb_blocks")
        assert blocks_dataset["status"] == "failed"
        assert blocks_dataset["status_label"] == "Failed"

        # Cleanup
        db_session.delete(failed_run)
        db_session.commit()

    def test_data_status_timestamp_formatting(self, client: TestClient, sample_data_status_runs):
        """Test that timestamps are properly formatted in HTML response."""
        response = client.get("/api/data-status")

        assert response.status_code == 200
        # Check for timestamp format (YYYY-MM-DD HH:MM:SS)
        # Should find at least one timestamp in the response
        import re
        timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, response.text)

    def test_data_status_source_metadata(self, client: TestClient):
        """Test that all datasets have source metadata displayed."""
        response = client.get("/api/api/data-status")

        assert response.status_code == 200
        data = response.json()

        for dataset in data["datasets"]:
            assert dataset["source"] in ["data.gov.sg", "OneMap API", "Calculated"]

    def test_data_status_next_ingest_schedule(self, client: TestClient):
        """Test that next ingestion schedule is displayed for all datasets."""
        response = client.get("/api/api/data-status")

        assert response.status_code == 200
        data = response.json()

        for dataset in data["datasets"]:
            assert dataset["next_ingest"]
            # Should contain time information
            assert "SGT" in dataset["next_ingest"] or "after" in dataset["next_ingest"].lower()
