"""Pytest configuration and fixtures."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.resalelens.database import Base, get_db
from src.resalelens.main import app

# Use in-memory SQLite database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
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
def client(test_db: Session) -> TestClient:
    """
    Create a FastAPI test client with test database override.
    
    Args:
        test_db: Test database session
        
    Returns:
        TestClient: FastAPI test client
    """
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
