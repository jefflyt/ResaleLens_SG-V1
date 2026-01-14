"""Integration tests for Fair Value calculation."""

from datetime import date, timedelta

import pytest

from resalelens.models import Block, Transaction
from resalelens.schemas.fair_value import FairValueRequest
from resalelens.services.fair_value import calculate_fair_value


class TestFairValueIntegration:
    """Integration tests for end-to-end Fair Value calculation."""

    @pytest.fixture
    def sample_block(self, db_session):
        """Create a sample block for testing."""
        block = Block(
            block="123",
            street="ANG MO KIO AVE 3",
            town="ANG MO KIO",
            latitude=1.3691,
            longitude=103.8454,
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)
        yield block
        # Cleanup
        db_session.delete(block)
        db_session.commit()

    @pytest.fixture
    def sample_transactions(self, db_session, sample_ingestion_run, sample_block):
        """Create sample transactions for testing."""
        transactions = []
        base_date = date.today() - timedelta(days=60)

        # Create 15 transactions for the block
        for i in range(15):
            txn = Transaction(
                date=base_date + timedelta(days=i * 4),
                block="123",
                street="ANG MO KIO AVE 3",
                flat_type="4 ROOM",
                storey_range=f"0{(i % 3) + 1} TO 0{(i % 3) + 3}",  # Vary storey ranges
                floor_area_sqm=90.0 + (i % 5),  # Vary floor areas slightly
                price=400000 + (i * 5000),  # Vary prices
                lease_commence_date=1990,
                town="ANG MO KIO",
                flat_model="Model A",
                latitude=1.3691,
                longitude=103.8454,
                block_id=sample_block.id,
                ingestion_run_id=sample_ingestion_run.id,
            )
            db_session.add(txn)
            transactions.append(txn)

        db_session.commit()
        yield transactions

        # Cleanup
        for txn in transactions:
            db_session.delete(txn)
        db_session.commit()

    def test_calculate_fair_value_with_sufficient_comps(
        self, db_session, sample_block, sample_transactions
    ):
        """Test Fair Value calculation with sufficient comps."""
        request = FairValueRequest(
            block="123",
            street="ANG MO KIO AVE 3",
            flat_type="4 ROOM",
            floor_area_sqm=90.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        result = calculate_fair_value(request, db_session)

        # Verify response structure
        assert result.fair_value_low > 0
        assert result.fair_value_mid > 0
        assert result.fair_value_high > 0
        assert result.fair_value_low < result.fair_value_mid < result.fair_value_high

        # Verify confidence
        assert 0 <= result.confidence_score <= 100
        assert result.confidence_score >= 20  # Should have sufficient data

        # Verify comps
        assert result.comp_count > 0
        assert len(result.comps) == result.comp_count

        # Verify explainability
        assert result.explainability is not None
        assert result.explainability.comp_count_after_outliers > 0
        assert "same_block" in result.explainability.fallback_used

    def test_calculate_fair_value_with_asking_price(
        self, db_session, sample_block, sample_transactions
    ):
        """Test Fair Value calculation with user asking price."""
        request = FairValueRequest(
            block="123",
            street="ANG MO KIO AVE 3",
            flat_type="4 ROOM",
            floor_area_sqm=90.0,
            storey_range="04 TO 06",
            time_window_months=12,
            user_asking_price=450000,  # Mid-range price
        )

        result = calculate_fair_value(request, db_session)

        # Verify user label is assigned
        assert result.user_label is not None
        assert result.user_label in [
            "Fair",
            "Slightly high",
            "Slightly low",
            "High risk (too high)",
            "High risk (too low)",
            "Insufficient data",
        ]

    def test_calculate_fair_value_no_comps(self, db_session, sample_block):
        """Test Fair Value calculation when no comps exist."""
        request = FairValueRequest(
            block="123",
            street="ANG MO KIO AVE 3",
            flat_type="5 ROOM",  # Different flat type with no data
            floor_area_sqm=120.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        result = calculate_fair_value(request, db_session)

        # With no comps, expect low confidence and zero band
        assert result.confidence_score < 20
        assert result.comp_count == 0


class TestFairValueEdgeCases:
    """Tests for edge cases in Fair Value calculation."""

    @pytest.fixture
    def block_with_outlier_transactions(self, db_session, sample_ingestion_run):
        """Create block with transactions including outliers."""
        block = Block(
            block="456",
            street="BISHAN ST 22",
            town="BISHAN",
            latitude=1.3521,
            longitude=103.8398,
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)

        transactions = []
        base_date = date.today() - timedelta(days=30)

        # Create normal transactions
        for i in range(8):
            txn = Transaction(
                date=base_date + timedelta(days=i * 3),
                block="456",
                street="BISHAN ST 22",
                flat_type="4 ROOM",
                storey_range="04 TO 06",
                floor_area_sqm=95.0,
                price=450000 + (i * 2000),  # Normal range
                lease_commence_date=1985,
                town="BISHAN",
                flat_model="Model A",
                latitude=1.3521,
                longitude=103.8398,
                block_id=block.id,
                ingestion_run_id=sample_ingestion_run.id,
            )
            db_session.add(txn)
            transactions.append(txn)

        # Add outliers
        outlier_high = Transaction(
            date=base_date,
            block="456",
            street="BISHAN ST 22",
            flat_type="4 ROOM",
            storey_range="04 TO 06",
            floor_area_sqm=95.0,
            price=700000,  # Very high outlier
            lease_commence_date=1985,
            town="BISHAN",
            flat_model="Model A",
            latitude=1.3521,
            longitude=103.8398,
            block_id=block.id,
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add(outlier_high)
        transactions.append(outlier_high)

        db_session.commit()
        yield block, transactions

        # Cleanup
        for txn in transactions:
            db_session.delete(txn)
        db_session.delete(block)
        db_session.commit()

    def test_outlier_removal(self, db_session, block_with_outlier_transactions):
        """Test that outliers are properly removed."""
        block, transactions = block_with_outlier_transactions

        request = FairValueRequest(
            block="456",
            street="BISHAN ST 22",
            flat_type="4 ROOM",
            floor_area_sqm=95.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        result = calculate_fair_value(request, db_session)

        # Outlier should be removed
        assert result.explainability.comp_count_before_outliers > result.comp_count
        assert result.comp_count >= result.explainability.comp_count_after_outliers

        # Fair Value should not be skewed by outlier
        assert result.fair_value_high < 600000  # Should not include 700k outlier


class TestFairValuePerformance:
    """Performance tests for Fair Value calculation."""

    @pytest.fixture
    def large_transaction_dataset(self, db_session, sample_ingestion_run):
        """Create a large dataset for performance testing."""
        # Note: This is a simplified version. In real scenario, load actual data.
        # For CI, keep it small but representative
        blocks = []
        transactions = []

        for block_num in range(5):  # 5 blocks
            block = Block(
                block=f"{100 + block_num}",
                street="TEST STREET",
                town="TEST TOWN",
                latitude=1.35 + (block_num * 0.01),
                longitude=103.84 + (block_num * 0.01),
            )
            db_session.add(block)
            blocks.append(block)

        db_session.commit()

        base_date = date.today() - timedelta(days=365)

        for block in blocks:
            for i in range(20):  # 20 transactions per block
                txn = Transaction(
                    date=base_date + timedelta(days=i * 10),
                    block=block.block,
                    street="TEST STREET",
                    flat_type="4 ROOM",
                    storey_range="04 TO 06",
                    floor_area_sqm=90.0,
                    price=400000 + (i * 3000),
                    lease_commence_date=1990,
                    town="TEST TOWN",
                    flat_model="Model A",
                    latitude=float(block.latitude) if block.latitude else None,
                    longitude=float(block.longitude) if block.longitude else None,
                    block_id=block.id,
                    ingestion_run_id=sample_ingestion_run.id,
                )
                db_session.add(txn)
                transactions.append(txn)

        db_session.commit()
        yield blocks, transactions

        # Cleanup
        for txn in transactions:
            db_session.delete(txn)
        for block in blocks:
            db_session.delete(block)
        db_session.commit()

    def test_performance(self, db_session, large_transaction_dataset):
        """Test Fair Value calculation performance."""
        import time

        blocks, transactions = large_transaction_dataset

        request = FairValueRequest(
            block="100",
            street="TEST STREET",
            flat_type="4 ROOM",
            floor_area_sqm=90.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        start = time.time()
        result = calculate_fair_value(request, db_session)
        elapsed = time.time() - start

        # Should complete within 2.5 seconds (p95 target from PSD)
        assert elapsed < 2.5

        # Verify result is valid
        assert result.fair_value_mid > 0
