"""Schemas for Data Status feature."""

from datetime import datetime

from pydantic import BaseModel


class DatasetStatus(BaseModel):
    """Dataset ingestion status information."""

    dataset_name: str
    source: str
    last_ingest: datetime | None
    next_ingest: str
    status: str  # "healthy", "delayed", "failed", "never_run"
    status_label: str  # "Healthy", "Delayed", "Failed", "Never Run"
