"""Data Status service for dataset freshness and ingestion health transparency."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..models import IngestionRun, IngestionStatus
from ..schemas.data_status import DatasetStatus

# Dataset metadata: source and next ingestion schedule
DATASET_METADATA = {
    "hdb_transactions": {
        "source": "data.gov.sg",
        "next_ingest": "Weekly Sunday 03:00 SGT",
        "staleness_threshold_hours": 48,  # Delayed if >48h old
    },
    "hdb_blocks": {
        "source": "data.gov.sg",
        "next_ingest": "Monthly 1st 03:30 SGT",
        "staleness_threshold_hours": 720,  # 30 days (monthly data, allow grace period)
    },
    "hdb_property_info": {
        "source": "data.gov.sg",
        "next_ingest": "Monthly 1st 03:30 SGT",
        "staleness_threshold_hours": 720,  # 30 days
    },
    "pois": {
        "source": "OneMap API",
        "next_ingest": "Monthly 1st 03:30 SGT",
        "staleness_threshold_hours": 720,  # 30 days
    },
    "block_pois": {
        "source": "Calculated",
        "next_ingest": "Monthly 1st 03:30 SGT (after POI ingestion)",
        "staleness_threshold_hours": 720,  # 30 days
    },
}


def get_data_status(session: Session) -> list[DatasetStatus]:
    """
    Get data status for all tracked datasets.

    Queries the ingestion_runs table for latest successful run per dataset,
    computes freshness, and determines status (Healthy/Delayed/Failed).

    Args:
        session: Database session

    Returns:
        List of DatasetStatus objects, one per tracked dataset
    """
    statuses: list[DatasetStatus] = []

    for dataset_name, metadata in DATASET_METADATA.items():
        # Query latest run for this dataset (regardless of status)
        latest_run = (
            session.query(IngestionRun)
            .filter(IngestionRun.dataset_name == dataset_name)
            .order_by(IngestionRun.started_at.desc())
            .first()
        )

        # Determine status
        if latest_run is None:
            # No runs ever
            status = "never_run"
            status_label = "Never Run"
            last_ingest = None
        elif latest_run.status == IngestionStatus.FAILED:
            # Latest run failed
            status = "failed"
            status_label = "Failed"
            last_ingest = latest_run.started_at
        elif latest_run.status == IngestionStatus.SUCCESS and latest_run.completed_at:
            # Successful run - check freshness
            last_ingest = latest_run.completed_at
            now = datetime.now(UTC)
            time_since_ingest = now - last_ingest

            threshold_hours: int = metadata["staleness_threshold_hours"]  # type: ignore[assignment]
            if time_since_ingest > timedelta(hours=threshold_hours):
                status = "delayed"
                status_label = "Delayed"
            else:
                status = "healthy"
                status_label = "Healthy"
        else:
            # In progress or other status
            status = "in_progress"
            status_label = "In Progress"
            last_ingest = latest_run.started_at

        statuses.append(
            DatasetStatus(
                dataset_name=dataset_name,
                source=str(metadata["source"]),
                last_ingest=last_ingest,
                next_ingest=str(metadata["next_ingest"]),
                status=status,
                status_label=status_label,
            )
        )

    return statuses
