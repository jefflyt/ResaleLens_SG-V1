"""Unit tests for Block X-Ray service - Transaction Analytics."""

import pytest
from datetime import UTC, datetime, timedelta

from resalelens.models import Block, Transaction
from resalelens.services.block_xray import (
    calculate_volatility,
    get_transaction_trends,
)


class TestTransactionTrends:
    """Tests for transaction trend calculation."""

    def test_get_transaction_trends_sufficient_data(self, db_session):
        """Test quarterly aggregation with sufficient transaction data."""
        # Create a block (let database assign ID)
        block = Block(
            block="123A",
            street="TEST TREND STREET",
            town="TEST TOWN",
            postal_code="998877",
        )
        db_session.add(block)
        db_session.flush()  # Get the auto-generated ID
        block_id = block.id

        # Create transactions over past 2 years (8 quarters)
        now = datetime.now(UTC)
        transactions = []

        # Q1 2024: 3 transactions with PSM~5000
        for i in range(3):
            txn = Transaction(
                block="123A",
                street="TEST TREND STREET",
                town="TEST TOWN",
                flat_type="4-ROOM",
                storey_range="07 TO 09",
                price=500000 + (i * 10000),
                floor_area_sqm=100.0,
                date=(now - timedelta(days=90 + i)).date(),
            )
            transactions.append(txn)

        # Q4 2023: 2 transactions with PSM~6000
        for i in range(2):
            txn = Transaction(
                block="123A",
                street="TEST TREND STREET",
                town="TEST TOWN",
                flat_type="4-ROOM",
                storey_range="07 TO 09",
                price=600000 + (i * 5000),
                floor_area_sqm=100.0,
                date=(now - timedelta(days=180 + i)).date(),
            )
            transactions.append(txn)

        db_session.add_all(transactions)
        db_session.commit()

        # Get trends
        trends = get_transaction_trends(block_id, db_session)

        # Verify we got data
        assert len(trends) > 0
        assert all(hasattr(t, "quarter") for t in trends)
        assert all(hasattr(t, "median_psm") for t in trends)
        assert all(t.median_psm > 0 for t in trends)

    def test_get_transaction_trends_insufficient_data(self, db_session):
        """Test that empty list is returned when <5 transactions."""
        # Create a block (let database assign ID)
        block = Block(
            block="456B",
            street="TEST TREND STREET 2",
            town="TEST TOWN",
            postal_code="776655",
        )
        db_session.add(block)
        db_session.flush()
        block_id = block.id

        # Create only 2 transactions (less than 5)
        now = datetime.now(UTC)
        for i in range(2):
            txn = Transaction(
                block="456B",
                street="TEST TREND STREET 2",
                town="TEST TOWN",
                flat_type="3-ROOM",
                storey_range="04 TO 06",
                price=500000,
                floor_area_sqm=100.0,
                date=(now - timedelta(days=30 + i)).date(),
            )
            db_session.add(txn)

        db_session.commit()

        # Get trends
        trends = get_transaction_trends(block_id, db_session)

        # Should return empty list
        assert trends == []

    def test_get_transaction_trends_block_not_found(self, db_session):
        """Test graceful handling when block doesn't exist."""
        trends = get_transaction_trends(99999, db_session)
        assert trends == []


class TestVolatilityCalculation:
    """Tests for volatility calculation."""

    def test_calculate_volatility_low(self, db_session):
        """Test low volatility (CV < 10%) classification."""
        # Create a block (let database assign ID)
        block = Block(
            block="789C",
            street="STABLE STREET TEST",
            town="TEST TOWN",
            postal_code="554433",
        )
        db_session.add(block)
        db_session.flush()
        block_id = block.id

        # Create 10 transactions with low variance (PSM around 5000 ± 200)
        now = datetime.now(UTC)
        for i in range(10):
            price_variation = (i % 5 - 2) * 20000  # Small variation
            txn = Transaction(
                block="789C",
                street="STABLE STREET TEST",
                town="TEST TOWN",
                flat_type="4-ROOM",
                storey_range="10 TO 12",
                price=500000 + price_variation,
                floor_area_sqm=100.0,
                date=(now - timedelta(days=30 * i)).date(),
            )
            db_session.add(txn)

        db_session.commit()

        # Calculate volatility
        volatility = calculate_volatility(block_id, db_session)

        # Should be low volatility
        assert volatility is not None
        assert volatility.classification == "low"
        assert volatility.label == "Stable Market"
        assert volatility.std_dev > 0

    def test_calculate_volatility_medium(self, db_session):
        """Test medium volatility (10% <= CV < 20%) classification."""
        # Create a block (let database assign ID)
        block = Block(
            block="321D",
            street="MODERATE STREET TEST",
            town="TEST TOWN",
            postal_code="332211",
        )
        db_session.add(block)
        db_session.flush()
        block_id = block.id

        # Create transactions with moderate variance
        now = datetime.now(UTC)
        prices = [400000, 500000, 450000, 550000, 480000, 520000, 460000, 540000]
        for i, price in enumerate(prices):
            txn = Transaction(
                block="321D",
                street="MODERATE STREET",
                town="TEST TOWN",
                flat_type="5-ROOM",
                storey_range="07 TO 09",
                price=price,
                floor_area_sqm=100.0,
                date=(now - timedelta(days=30 * i)).date(),
            )
            db_session.add(txn)

        db_session.commit()

        # Calculate volatility
        volatility = calculate_volatility(block_id, db_session)

        # Should be medium volatility
        assert volatility is not None
        assert volatility.classification == "medium"
        assert volatility.label == "Moderate Fluctuation"

    def test_calculate_volatility_high(self, db_session):
        """Test high volatility (CV >= 20%) classification."""
        # Create a block (let database assign ID)
        block = Block(
            block="654E",
            street="VOLATILE STREET TEST",
            town="TEST TOWN",
            postal_code="665544",
        )
        db_session.add(block)
        db_session.flush()
        block_id = block.id

        # Create transactions with high variance
        now = datetime.now(UTC)
        prices = [300000, 700000, 350000, 650000, 400000, 600000, 320000, 680000]
        for i, price in enumerate(prices):
            txn = Transaction(
                block="654E",
                street="VOLATILE STREET TEST",
                town="TEST TOWN",
                flat_type="EXECUTIVE",
                storey_range="04 TO 06",
                price=price,
                floor_area_sqm=100.0,
                date=(now - timedelta(days=30 * i)).date(),
            )
            db_session.add(txn)

        db_session.commit()

        # Calculate volatility
        volatility = calculate_volatility(block_id, db_session)

        # Should be high volatility
        assert volatility is not None
        assert volatility.classification == "high"
        assert volatility.label == "High Volatility"

    def test_calculate_volatility_insufficient_data(self, db_session):
        """Test that None is returned when <5 transactions."""
        # Create a block (let database assign ID)
        block = Block(
            block="987F",
            street="FEW TRANSACTIONS STREET TEST",
            town="TEST TOWN",
            postal_code="887766",
        )
        db_session.add(block)
        db_session.flush()
        block_id = block.id

        # Create only 3 transactions
        now = datetime.now(UTC)
        for i in range(3):
            txn = Transaction(
                block="987F",
                street="FEW TRANSACTIONS STREET TEST",
                town="TEST TOWN",
                flat_type="3-ROOM",
                storey_range="01 TO 03",
                price=500000,
                floor_area_sqm=100.0,
                date=(now - timedelta(days=30 * i)).date(),
            )
            db_session.add(txn)

        db_session.commit()

        # Calculate volatility
        volatility = calculate_volatility(block_id, db_session)

        # Should return None
        assert volatility is None

    def test_calculate_volatility_block_not_found(self, db_session):
        """Test graceful handling when block doesn't exist."""
        volatility = calculate_volatility(99999, db_session)
        assert volatility is None
