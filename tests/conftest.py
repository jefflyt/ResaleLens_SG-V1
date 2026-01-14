"""Pytest configuration and fixtures."""

import os
from collections.abc import Generator
from datetime import datetime

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Load test environment
load_dotenv(".env.local")

from resalelens.database import get_db
from resalelens.main import app
from resalelens.models import IngestionRun, IngestionStatus

# Use PostgreSQL test database (Supabase)
# Priority: DATABASE_URL_TEST > DATABASE_URL with test schema
database_url = os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError(
        "DATABASE_URL or DATABASE_URL_TEST must be set for tests. "
        "Add to .env.local:\n"
        "  DATABASE_URL=postgresql://...\n"
        "  DATABASE_URL_TEST=postgresql://... (optional, for test isolation)"
    )

# Create test engine
engine = create_engine(database_url)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a test database session with automatic rollback.

    Uses nested transactions (SAVEPOINT) to ensure test isolation.
    Each test runs in its own transaction that gets rolled back after the test.

    Yields:
        Session: Test database session
    """
    # Create a connection
    connection = engine.connect()

    # Begin a non-ORM transaction
    transaction = connection.begin()

    # Create a session bound to the connection
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (uses SAVEPOINT in PostgreSQL)
    nested = connection.begin_nested()

    # If the application code calls session.commit(), it will end the nested
    # transaction but not commit the outer transaction
    @event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        # Roll back the overall transaction, restoring pre-test state
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """
    Create a FastAPI test client with test database override.

    Args:
        db_session: Test database session

    Returns:
        TestClient: FastAPI test client
    """

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_ingestion_run(db_session: Session) -> IngestionRun:
    """
    Create a sample ingestion run for testing.

    Args:
        db_session: Test database session

    Returns:
        IngestionRun: Sample ingestion run
    """
    run = IngestionRun(
        dataset_name="test_transactions",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        status=IngestionStatus.SUCCESS,
        rows_processed=0,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run
