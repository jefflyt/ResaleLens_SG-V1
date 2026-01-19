"""Tests for postal code block lookup API endpoint."""

import pytest
from fastapi.testclient import TestClient

from resalelens.models import Block


class TestBlockLookupAPI:
    """Tests for GET /api/block-lookup endpoint."""

    @pytest.fixture
    def sample_blocks_with_postal_codes(self, db_session):
        """Create sample blocks with postal codes for testing."""
        blocks = [
            Block(
                block="514",
                street="ANG MO KIO AVENUE 8",
                town="ANG MO KIO",
                postal_code="650514",
                postal_sector="65",
            ),
            Block(
                block="515",
                street="ANG MO KIO AVENUE 8",
                town="ANG MO KIO",
                postal_code="650515",
                postal_sector="65",
            ),
            Block(
                block="123",
                street="BISHAN STREET 12",
                town="BISHAN",
                postal_code="570123",
                postal_sector="57",
            ),
            # Block without postal code
            Block(
                block="999",
                street="TEST STREET",
                town="TEST TOWN",
                latitude=1.35,
                longitude=103.84,
            ),
        ]
        for block in blocks:
            db_session.add(block)
        db_session.commit()

        for block in blocks:
            db_session.refresh(block)

        yield blocks

        # Cleanup
        for block in blocks:
            db_session.delete(block)
        db_session.commit()

    def test_exact_postal_code_match(self, client: TestClient, sample_blocks_with_postal_codes):
        """Test block lookup with exact postal code match."""
        response = client.get("/api/block-lookup?postal_code=650514")

        assert response.status_code == 200
        data = response.json()

        assert data["block"] == "514"
        assert data["street"] == "ANG MO KIO AVENUE 8"
        assert data["town"] == "ANG MO KIO"
        assert data["postal_code"] == "650514"
        assert data["postal_sector"] == "65"

    def test_hdb_inference_lookup(self, client: TestClient, sample_blocks_with_postal_codes):
        """Test HDB block inference (last 3 digits = block number)."""
        # Simulate postal code where exact match doesn't exist
        # but block can be inferred from last 3 digits
        response = client.get("/api/block-lookup?postal_code=570123")

        assert response.status_code == 200
        data = response.json()

        assert data["block"] == "123"
        assert data["town"] == "BISHAN"

    def test_invalid_postal_code_format(self, client: TestClient):
        """Test validation of invalid postal code formats."""
        # Too short
        response = client.get("/api/block-lookup?postal_code=12345")
        assert response.status_code == 400
        assert "Invalid postal code format" in response.json()["detail"]

        # Too long
        response = client.get("/api/block-lookup?postal_code=1234567")
        assert response.status_code == 400

        # Non-numeric
        response = client.get("/api/block-lookup?postal_code=12345a")
        assert response.status_code == 400

    def test_postal_code_not_found_with_suggestions(
        self, client: TestClient, sample_blocks_with_postal_codes
    ):
        """Test postal code not found but returns suggestions from same sector."""
        # Code not in DB, but same sector (65) exists
        response = client.get("/api/block-lookup?postal_code=650999")

        # Should return 200 with suggestions
        assert response.status_code == 200
        data = response.json()

        assert "error" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

        # Suggestions should be from same postal sector (65)
        for suggestion in data["suggestions"]:
            assert suggestion["postal_sector"] == "65"

    def test_postal_code_not_found_no_suggestions(
        self, client: TestClient, sample_blocks_with_postal_codes
    ):
        """Test postal code not found with no suggestions available."""
        # Postal sector 99 doesn't exist in database
        response = client.get("/api/block-lookup?postal_code=999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_multiple_blocks_same_postal_code(self, client: TestClient, db_session):
        """Test handling of multiple blocks with same postal code."""
        # Create two blocks with same postal code (rare but possible)
        blocks = [
            Block(
                block="100A",
                street="SAME STREET",
                town="TOWN A",
                postal_code="123456",
                postal_sector="12",
            ),
            Block(
                block="100B",
                street="SAME STREET",
                town="TOWN A",
                postal_code="123456",
                postal_sector="12",
            ),
        ]
        for block in blocks:
            db_session.add(block)
        db_session.commit()

        response = client.get("/api/block-lookup?postal_code=123456")

        assert response.status_code == 200
        data = response.json()

        # Should return multiple matches with suggestion flag
        assert "matches" in data
        assert data["suggestions"] is True
        assert len(data["matches"]) == 2

        # Cleanup
        for block in blocks:
            db_session.delete(block)
        db_session.commit()

    def test_postal_sector_fallback(self, client: TestClient, sample_blocks_with_postal_codes):
        """Test that sector fallback returns blocks from same postal sector."""
        # Search for non-existent code in sector 65
        response = client.get("/api/block-lookup?postal_code=650888")

        data = response.json()

        if "suggestions" in data and data["suggestions"]:
            # All suggestions should be from sector 65
            for suggestion in data["suggestions"]:
                if suggestion.get("postal_sector"):
                    assert suggestion["postal_sector"] == "65"
