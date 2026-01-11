"""Pytest configuration and fixtures."""

from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from resalelens.database import Base, get_db
from resalelens.main import app
from resalelens.models import IngestionRun, IngestionStatus

# Use in-memory SQLite database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable foreign key constraints for SQLite
from sqlalchemy import event


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Create a test database session.

    Yields:
        Session: Test database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


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
