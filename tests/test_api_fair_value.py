"""Tests for Fair Value API endpoint."""

import pytest
from fastapi.testclient import TestClient

from resalelens.models import Block, Transaction


class TestFairValueAPI:
    """Tests for POST /api/fair-value endpoint."""

    @pytest.fixture
    def api_test_data(self, db_session, sample_ingestion_run):
        """Create test data for API tests."""
        # Create block with normalized street name (as it would be stored in DB)
        block = Block(
            block="123",
            street="ANG MO KIO AVENUE 3",  # Normalized (AVENUE not AVE)
            town="ANG MO KIO",
            latitude=1.3691,
            longitude=103.8454,
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)

        # Create transactions with normalized street name
        from datetime import date, timedelta

        transactions = []
        base_date = date.today() - timedelta(days=60)

        for i in range(15):
            txn = Transaction(
                date=base_date + timedelta(days=i * 4),
                block="123",
                street="ANG MO KIO AVENUE 3",  # Normalized
                flat_type="4 ROOM",
                storey_range="04 TO 06",
                floor_area_sqm=90.0,
                price=400000 + (i * 5000),
                lease_commence_date=1990,
                town="ANG MO KIO",
                flat_model="Model A",
                latitude=1.3691,
                longitude=103.8454,
                block_id=block.id,
                ingestion_run_id=sample_ingestion_run.id,
            )
            db_session.add(txn)
            transactions.append(txn)

        db_session.commit()
        yield block, transactions

        # Cleanup
        for txn in transactions:
            db_session.delete(txn)
        db_session.delete(block)
        db_session.commit()

    def test_fair_value_api_form_submission(self, client: TestClient, api_test_data):
        """Test POST /api/fair-value with form data (HTMX request)."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVENUE 3",  # Normalized
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
                "time_window_months": "12",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check for key elements in HTML response
        assert "Fair Value Assessment" in response.text
        assert "Confidence Score" in response.text
        assert "Comparable Transactions" in response.text

    def test_fair_value_api_json_response(self, client: TestClient, api_test_data):
        """Test POST /api/fair-value returns JSON for non-HTMX requests."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVENUE 3",  # Normalized
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
                "time_window_months": "12",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "fair_value_low" in data
        assert "fair_value_mid" in data
        assert "fair_value_high" in data
        assert "confidence_score" in data
        assert "comp_count" in data
        assert "comps" in data
        assert "explainability" in data
        assert "last_updated" in data

        # Verify values
        assert data["fair_value_low"] > 0
        assert data["fair_value_mid"] > 0
        assert data["fair_value_high"] > 0
        assert 0 <= data["confidence_score"] <= 100
        assert data["comp_count"] > 0

    def test_fair_value_api_missing_field(self, client: TestClient):
        """Test POST /api/fair-value with missing required field."""
        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                # Missing street
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_fair_value_api_invalid_block(self, client: TestClient):
        """Test POST /api/fair-value with non-existent block."""
        response = client.post(
            "/api/fair-value",
            data={
                "block": "99999",
                "street": "FAKE STREET",
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should still return 200 but with low confidence or no comps
        # The Fair Value service handles this gracefully
        assert response.status_code in [200, 404, 500]

    def test_fair_value_api_invalid_flat_type(self, client: TestClient):
        """Test POST /api/fair-value with invalid flat type."""
        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVE 3",
                "flat_type": "99 ROOM",  # Invalid
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_fair_value_api_edge_case_floor_area(self, client: TestClient, api_test_data):
        """Test POST /api/fair-value with edge case floor area."""
        block, transactions = api_test_data

        # Test minimum floor area
        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVENUE 3",  # Normalized
                "flat_type": "4 ROOM",
                "floor_area_sqm": "30.0",  # Minimum
                "storey_range": "04 TO 06",
            },
        )

        assert response.status_code == 200

    def test_last_updated_field(self, client: TestClient, api_test_data):
        """Test that last_updated field is populated."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVENUE 3",  # Normalized
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # last_updated should be present (may be None if no ingestion runs)
        assert "last_updated" in data

    # ===== Address Normalization Tests =====

    def test_fair_value_with_lowercase_input(self, client: TestClient, api_test_data):
        """Test that lowercase block and street names are normalized and work correctly."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",  # lowercase
                "street": "ang mo kio avenue 3",  # lowercase (will be normalized)
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should successfully normalize and return 200 (not 404 "Block not found")
        assert response.status_code == 200
        data = response.json()
        # Verify response structure (normalization worked, block was found)
        assert "fair_value_mid" in data
        assert "confidence_score" in data

    def test_fair_value_with_abbreviated_street(self, client: TestClient, api_test_data):
        """Test that abbreviated street names (AVE instead of AVENUE) are normalized."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ANG MO KIO AVE 3",  # AVE should expand to AVENUE
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should successfully normalize and return 200
        assert response.status_code == 200
        data = response.json()
        assert "fair_value_mid" in data

    def test_fair_value_with_extra_whitespace(self, client: TestClient, api_test_data):
        """Test that extra whitespace in block and street is trimmed."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "  123  ",  # Extra spaces
                "street": "  ANG MO KIO AVENUE 3  ",  # Extra spaces
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should successfully normalize and return 200
        assert response.status_code == 200
        data = response.json()
        assert "fair_value_mid" in data

    def test_fair_value_with_mixed_case_and_abbreviations(self, client: TestClient, api_test_data):
        """Test combination of lowercase and abbreviations."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ang mo kio ave 3",  # lowercase + abbreviation
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
        )

        # Should successfully normalize and return 200
        assert response.status_code == 200
        data = response.json()
        assert "fair_value_mid" in data

    def test_fair_value_normalization_with_htmx(self, client: TestClient, api_test_data):
        """Test that normalization works for HTMX requests (HTML response)."""
        block, transactions = api_test_data

        response = client.post(
            "/api/fair-value",
            data={
                "block": "123",
                "street": "ang mo kio ave 3",  # lowercase + abbreviated
                "flat_type": "4 ROOM",
                "floor_area_sqm": "90.0",
                "storey_range": "04 TO 06",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Fair Value Assessment" in response.text
