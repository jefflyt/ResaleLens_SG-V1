"""Utilities for data ingestion: retry logic, logging, API helpers."""

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

import httpx
from sqlalchemy.orm import Session

from ..data.repositories import IngestionRunRepository
from ..models import IngestionRun, IngestionStatus

T = TypeVar("T")


def retry_on_failure(
    max_retries: int = 3,
    initial_delay: float = 5.0,
    exponential_base: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying function calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        exponential_base: Base for exponential backoff calculation

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = initial_delay * (exponential_base**attempt)
                        print(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        print(f"All {max_retries + 1} attempts failed. Giving up.")

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed without exception")

        return wrapper

    return decorator


@contextmanager
def log_ingestion_run(
    session: Session, dataset_name: str
) -> Generator[IngestionRun, None, None]:
    """
    Context manager for logging ingestion runs.

    Creates an IngestionRun record at start, updates on success/failure.

    Args:
        session: SQLAlchemy session
        dataset_name: Name of the dataset being ingested

    Yields:
        IngestionRun instance for tracking

    Example:
        with log_ingestion_run(session, "hdb_transactions") as run:
            # Perform ingestion
            run.rows_processed = 100
    """
    repo = IngestionRunRepository(session)

    # Create ingestion run record
    run = repo.create(
        dataset_name=dataset_name,
        started_at=datetime.utcnow(),
        status=IngestionStatus.IN_PROGRESS,
        rows_processed=0,
    )

    try:
        yield run
        # Success - update status
        run.status = IngestionStatus.SUCCESS
        run.completed_at = datetime.utcnow()
        repo.update(run)
    except Exception as e:
        # Failure - log error
        run.status = IngestionStatus.FAILED
        run.completed_at = datetime.utcnow()
        run.error_summary = f"{type(e).__name__}: {str(e)}"
        repo.update(run)
        raise


def fetch_json_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Fetch JSON from URL with retry logic.

    Args:
        url: URL to fetch
        params: Query parameters
        headers: HTTP headers
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Returns:
        JSON response as dictionary

    Raises:
        httpx.HTTPError: If request fails after retries
    """

    @retry_on_failure(max_retries=max_retries)
    def _fetch() -> dict[str, Any]:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    return _fetch()


def parse_date(date_string: str) -> datetime:
    """
    Parse date string from various formats.

    Supports:
    - YYYY-MM-DD
    - YYYY-MM
    - DD/MM/YYYY

    Args:
        date_string: Date string to parse

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date format is not recognized
    """
    # Try YYYY-MM-DD
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        pass

    # Try YYYY-MM (assume first day of month)
    try:
        return datetime.strptime(date_string, "%Y-%m")
    except ValueError:
        pass

    # Try DD/MM/YYYY
    try:
        return datetime.strptime(date_string, "%d/%m/%Y")
    except ValueError:
        pass

    raise ValueError(f"Unsupported date format: {date_string}")


def validate_transaction_record(record: dict[str, Any]) -> bool:
    """
    Validate that a transaction record has all required fields.

    Args:
        record: Transaction record dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "month",
        "block",
        "street_name",
        "flat_type",
        "storey_range",
        "floor_area_sqm",
        "resale_price",
        "lease_commence_date",
        "town",
        "flat_model",
    ]

    for field in required_fields:
        if field not in record or record[field] is None or record[field] == "":
            return False

    return True
