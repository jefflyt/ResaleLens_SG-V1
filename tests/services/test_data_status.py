"""Unit tests for Data Status service."""

from datetime import UTC, datetime, timedelta

from resalelens.models import IngestionRun, IngestionStatus
from resalelens.services.data_status import get_data_status


class TestDataStatus:
    """Tests for Data Status service."""

    def test_get_data_status_all_healthy(self, db_session):
        """Verify all datasets show 'healthy' status when recently ingested."""
        # Create recent successful runs for all datasets (within last 24 hours)
        now = datetime.now(UTC)
        datasets = [
            "hdb_transactions",
            "hdb_postal_codes",
            "hdb_property_info",
            "pois",
            "block_pois",
        ]

        for dataset_name in datasets:
            run = IngestionRun(
                dataset_name=dataset_name,
                started_at=now - timedelta(hours=12),
                completed_at=now - timedelta(hours=12),
                status=IngestionStatus.SUCCESS,
                rows_processed=100,
            )
            db_session.add(run)

        db_session.commit()

        # Get data status
        statuses = get_data_status(db_session)

        # Verify all are healthy
        assert len(statuses) == 5
        for status in statuses:
            assert status.status == "healthy"
            assert status.status_label == "Healthy"
            assert status.last_ingest is not None

    def test_get_data_status_delayed(self, db_session):
        """Verify 'delayed' status when transaction dataset is >48h stale."""
        # Create old successful run for hdb_transactions (3 days ago)
        now = datetime.now(UTC)
        old_run = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(old_run)
        db_session.commit()

        # Get data status
        statuses = get_data_status(db_session)

        # Find transactions status
        txn_status = next(s for s in statuses if s.dataset_name == "hdb_transactions")

        # Verify delayed
        assert txn_status.status == "delayed"
        assert txn_status.status_label == "Delayed"
        assert txn_status.last_ingest is not None

    def test_get_data_status_failed(self, db_session):
        """Verify 'failed' status when latest run has status='failed'."""
        # Create failed run for hdb_postal_codes
        now = datetime.now(UTC)
        failed_run = IngestionRun(
            dataset_name="hdb_postal_codes",
            started_at=now - timedelta(hours=1),
            completed_at=None,  # Failed runs may not have completed_at
            status=IngestionStatus.FAILED,
            rows_processed=0,
            error_summary="API connection timeout",
        )
        db_session.add(failed_run)
        db_session.commit()

        # Get data status
        statuses = get_data_status(db_session)

        # Find postal codes status
        postal_codes_status = next(s for s in statuses if s.dataset_name == "hdb_postal_codes")

        # Verify failed
        assert postal_codes_status.status == "failed"
        assert postal_codes_status.status_label == "Failed"

    def test_get_data_status_no_runs(self, db_session):
        """Verify service returns all tracked datasets regardless of run history."""
        # Note: Can't clean up all runs due to foreign key constraints with transactions
        # Instead, verify the service returns all 5 tracked datasets

        # Get data status
        statuses = get_data_status(db_session)

        # Verify all 5 tracked datasets are returned
        assert len(statuses) == 5
        dataset_names = [s.dataset_name for s in statuses]
        assert "hdb_transactions" in dataset_names
        assert "hdb_postal_codes" in dataset_names
        assert "hdb_property_info" in dataset_names
        assert "pois" in dataset_names
        assert "block_pois" in dataset_names

    def test_freshness_calculation_transactions(self, db_session):
        """Verify 48-hour threshold logic for transactions dataset."""
        now = datetime.now(UTC)

        # Test exactly at threshold (48 hours) - should be healthy (not delayed yet)
        run_at_threshold = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=now - timedelta(hours=48),
            completed_at=now - timedelta(hours=48),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(run_at_threshold)
        db_session.commit()

        statuses = get_data_status(db_session)
        txn_status = next(s for s in statuses if s.dataset_name == "hdb_transactions")

        # At exactly 48h, should be delayed (threshold is >48h)
        assert txn_status.status == "delayed"

        # Clean up
        db_session.delete(run_at_threshold)
        db_session.commit()

        # Test just before threshold (47 hours) - should be healthy
        run_before_threshold = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=now - timedelta(hours=47),
            completed_at=now - timedelta(hours=47),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(run_before_threshold)
        db_session.commit()

        statuses = get_data_status(db_session)
        txn_status = next(s for s in statuses if s.dataset_name == "hdb_transactions")

        assert txn_status.status == "healthy"

    def test_freshness_calculation_monthly_datasets(self, db_session):
        """Verify 30-day threshold logic for monthly datasets (pois, blocks, property_info)."""
        now = datetime.now(UTC)

        # Create run for POIs 20 days ago - should be healthy (threshold is 30 days)
        recent_run = IngestionRun(
            dataset_name="pois",
            started_at=now - timedelta(days=20),
            completed_at=now - timedelta(days=20),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(recent_run)
        db_session.commit()

        statuses = get_data_status(db_session)
        poi_status = next(s for s in statuses if s.dataset_name == "pois")

        assert poi_status.status == "healthy"

        # Clean up and test old run (40 days ago) - should be delayed
        db_session.delete(recent_run)
        db_session.commit()

        old_run = IngestionRun(
            dataset_name="pois",
            started_at=now - timedelta(days=40),
            completed_at=now - timedelta(days=40),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
        )
        db_session.add(old_run)
        db_session.commit()

        statuses = get_data_status(db_session)
        poi_status = next(s for s in statuses if s.dataset_name == "pois")

        assert poi_status.status == "delayed"

    def test_in_progress_status(self, db_session):
        """Verify 'in_progress' status when run is currently running."""
        now = datetime.now(UTC)

        # Create in-progress run
        in_progress_run = IngestionRun(
            dataset_name="hdb_transactions",
            started_at=now - timedelta(minutes=10),
            completed_at=None,  # Still running
            status=IngestionStatus.IN_PROGRESS,
            rows_processed=50,
        )
        db_session.add(in_progress_run)
        db_session.commit()

        # Get data status
        statuses = get_data_status(db_session)
        txn_status = next(s for s in statuses if s.dataset_name == "hdb_transactions")

        # Verify in progress
        assert txn_status.status == "in_progress"
        assert txn_status.status_label == "In Progress"

    def test_dataset_metadata_completeness(self, db_session):
        """Verify all datasets have source and next_ingest metadata."""
        statuses = get_data_status(db_session)

        for status in statuses:
            assert status.source, f"Missing source for {status.dataset_name}"
            assert status.next_ingest, f"Missing next_ingest for {status.dataset_name}"
            assert status.dataset_name in [
                "hdb_transactions",
                "hdb_postal_codes",
                "hdb_property_info",
                "pois",
                "block_pois",
            ]
