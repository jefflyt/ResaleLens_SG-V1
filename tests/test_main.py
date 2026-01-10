"""Tests for main application routes."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page(client: TestClient) -> None:
    """Test the home page renders successfully."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "ResaleLens SG" in response.text


def test_home_page_contains_features(client: TestClient) -> None:
    """Test that home page contains feature descriptions."""
    response = client.get("/")

    assert response.status_code == 200
    assert "Fair Value Engine" in response.text
    assert "Block X-Ray" in response.text
    assert "Smart Comparisons" in response.text
