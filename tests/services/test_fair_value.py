"""Unit tests for Fair Value calculation service."""

from datetime import date, timedelta
from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest

from resalelens.models import Transaction
from resalelens.schemas.fair_value import FairValueRequest
from resalelens.services.fair_value import (
    assign_user_label,
    build_explainability,
    calculate_confidence,
    generate_fair_value_band,
    normalize_comps,
    remove_outliers,
    select_comps,
)
from resalelens.services.utils import (
    calculate_median_by_storey,
    haversine_distance,
    parse_storey_range,
)


class TestUtils:
    """Tests for utility functions."""

    def test_haversine_distance(self):
        """Test Haversine distance calculation."""
        # Distance between two known points in Singapore
        # Ang Mo Kio (1.3691, 103.8454) to Bishan (1.3521, 103.8398)
        dist = haversine_distance(1.3691, 103.8454, 1.3521, 103.8398)
        # Should be approximately 2km
        assert 1500 < dist < 2500

    def test_parse_storey_range(self):
        """Test storey range parsing."""
        assert parse_storey_range("04 TO 06") == 5
        assert parse_storey_range("01 TO 03") == 2
        assert parse_storey_range("10 TO 12") == 11

    def test_parse_storey_range_invalid(self):
        """Test storey range parsing with invalid input."""
        with pytest.raises(ValueError):
            parse_storey_range("INVALID")

    def test_calculate_median_by_storey(self):
        """Test median calculation by storey."""
        df = pd.DataFrame(
            {
                "storey_midpoint": [2, 2, 5, 5, 8, 8],
                "psm": [4000, 4200, 4500, 4600, 5000, 5200],
            }
        )
        medians = calculate_median_by_storey(df)
        assert medians[2] == 4100
        assert medians[5] == 4550
        assert medians[8] == 5100


class TestNormalization:
    """Tests for comp normalization."""

    def test_normalize_comps_basic(self):
        """Test basic psm normalization."""
        # Create mock transactions
        txns = [
            Mock(
                spec=Transaction,
                date=date.today(),
                price=400000,
                floor_area_sqm=100,
                storey_range="04 TO 06",
                flat_model="Model A",
                latitude=1.35,
                longitude=103.84,
            ),
            Mock(
                spec=Transaction,
                date=date.today(),
                price=450000,
                floor_area_sqm=110,
                storey_range="07 TO 09",
                flat_model="Model A",
                latitude=1.35,
                longitude=103.84,
            ),
        ]

        df = normalize_comps(txns, "04 TO 06")

        assert len(df) == 2
        assert "psm" in df.columns
        assert "adjusted_psm" in df.columns
        assert df.iloc[0]["psm"] == 4000.0
        assert df.iloc[1]["psm"] == pytest.approx(4090.91, rel=0.01)

    def test_normalize_comps_empty(self):
        """Test normalization with empty comp list."""
        df = normalize_comps([], "04 TO 06")
        assert df.empty


class TestOutlierRemoval:
    """Tests for outlier removal."""

    def test_remove_outliers_percentile(self):
        """Test percentile-based outlier removal."""
        # Create DataFrame with outliers
        df = pd.DataFrame(
            {
                "adjusted_psm": [
                    4000,
                    4100,
                    4200,
                    4150,
                    4250,
                    6000,
                    2000,
                ]  # 6000 and 2000 are outliers
            }
        )

        filtered = remove_outliers(df, method="percentile")

        # Outliers should be removed
        assert len(filtered) < len(df)
        assert filtered["adjusted_psm"].max() < 6000
        assert filtered["adjusted_psm"].min() > 2000

    def test_remove_outliers_mad(self):
        """Test MAD-based outlier removal."""
        df = pd.DataFrame({"adjusted_psm": [4000, 4100, 4200, 4150, 4250, 8000]})

        filtered = remove_outliers(df, method="mad")

        # Extreme outlier should be removed
        assert len(filtered) < len(df)
        assert filtered["adjusted_psm"].max() < 8000

    def test_remove_outliers_insufficient_data(self):
        """Test outlier removal with insufficient data."""
        df = pd.DataFrame({"adjusted_psm": [4000, 4100]})

        filtered = remove_outliers(df, method="percentile")

        # Should return all data when < 3 records
        assert len(filtered) == 2


class TestConfidenceScoring:
    """Tests for confidence score calculation."""

    def test_confidence_high_comp_count(self):
        """Test confidence with high comp count."""
        df = pd.DataFrame(
            {
                "adjusted_psm": [4000 + i * 10 for i in range(25)],  # 25 comps
                "date": [date.today() - timedelta(days=30) for _ in range(25)],
            }
        )

        score = calculate_confidence(df, 12)

        # Should get high score for 25 comps + low variance + recent
        assert score >= 80

    def test_confidence_low_comp_count(self):
        """Test confidence with low comp count."""
        df = pd.DataFrame(
            {
                "adjusted_psm": [4000, 4100, 4200],  # Only 3 comps
                "date": [date.today() - timedelta(days=200) for _ in range(3)],
            }
        )

        score = calculate_confidence(df, 12)

        # Should get lower score for 3 comps + older data
        assert score <= 50

    def test_confidence_high_variance(self):
        """Test confidence with high variance."""
        df = pd.DataFrame(
            {
                "adjusted_psm": [4000, 5000, 6000, 7000, 8000],  # High variance
                "date": [date.today() for _ in range(5)],
            }
        )

        score = calculate_confidence(df, 12)

        # Variance penalty should reduce score
        assert score < 70


class TestFairValueBand:
    """Tests for Fair Value band generation."""

    def test_generate_fair_value_band(self):
        """Test Fair Value band calculation."""
        df = pd.DataFrame({"adjusted_psm": [4000, 4100, 4200, 4300, 4400, 4500, 4600]})

        low, mid, high = generate_fair_value_band(df, 100)

        # For 100 sqm, P25 and P75 should create a reasonable band
        assert low < mid < high
        assert 400000 < low < 450000
        assert 420000 <= mid <= 480000  # More lenient mid range
        assert 440000 < high < 500000  # P75 is around 445000

    def test_generate_fair_value_band_empty(self):
        """Test Fair Value band with empty DataFrame."""
        df = pd.DataFrame()

        low, mid, high = generate_fair_value_band(df, 100)

        assert low == 0.0
        assert mid == 0.0
        assert high == 0.0


class TestUserLabel:
    """Tests for user label assignment."""

    def test_label_fair(self):
        """Test 'Fair' label."""
        label = assign_user_label(450000, 400000, 500000, 80)
        assert label == "Fair"

    def test_label_slightly_high(self):
        """Test 'Slightly high' label."""
        # Within 10% of upper bound
        label = assign_user_label(520000, 400000, 500000, 80)
        assert label == "Slightly high"

    def test_label_high_risk_too_high(self):
        """Test 'High risk (too high)' label."""
        # More than 10% above upper bound
        label = assign_user_label(600000, 400000, 500000, 80)
        assert label == "High risk (too high)"

    def test_label_slightly_low(self):
        """Test 'Slightly low' label."""
        # Within 10% of lower bound
        label = assign_user_label(380000, 400000, 500000, 80)
        assert label == "Slightly low"

    def test_label_high_risk_too_low(self):
        """Test 'High risk (too low)' label."""
        # More than 10% below lower bound
        label = assign_user_label(300000, 400000, 500000, 80)
        assert label == "High risk (too low)"

    def test_label_insufficient_data(self):
        """Test 'Insufficient data' label."""
        label = assign_user_label(450000, 400000, 500000, 15)
        assert label == "Insufficient data"

    def test_label_no_asking_price(self):
        """Test label when no asking price provided."""
        label = assign_user_label(None, 400000, 500000, 80)
        assert label == "Fair Value calculated"


class TestExplainability:
    """Tests for explainability output."""

    def test_build_explainability(self):
        """Test explainability output generation."""
        df_after = pd.DataFrame(
            {
                "adjusted_psm": [4000, 4100, 4200],
                "date": [date.today() - timedelta(days=i * 30) for i in range(3)],
            }
        )
        df_before = pd.DataFrame(
            {
                "adjusted_psm": [4000, 4100, 4200, 6000],  # 6000 removed as outlier
                "date": [date.today() - timedelta(days=i * 30) for i in range(4)],
            }
        )

        request = FairValueRequest(
            block="123",
            street="ANG MO KIO AVE 3",
            flat_type="4 ROOM",
            floor_area_sqm=90.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        explainability = build_explainability(df_after, df_before, "same_block_12m", request)

        assert explainability.comp_count_before_outliers == 4
        assert explainability.comp_count_after_outliers == 3
        assert explainability.fallback_used == "same_block_12m"
        assert "block" in explainability.filters_applied
        assert explainability.variance_cv >= 0


class TestSelectComps:
    """Tests for comp selection ladder."""

    def test_select_comps_tier1(self, monkeypatch):
        """Test tier 1 comp selection (same block, 12m)."""
        # Create a mock repository instance
        mock_repo = MagicMock()
        mock_repo.get_transactions_by_block.return_value = [
            Mock(spec=Transaction) for _ in range(10)
        ]

        # Mock the TransactionRepository class constructor
        def mock_transaction_repo_init(session):
            return mock_repo

        monkeypatch.setattr(
            "resalelens.services.fair_value.TransactionRepository", mock_transaction_repo_init
        )

        # Also mock BlockRepository for safety
        mock_block_repo = MagicMock()

        def mock_block_repo_init(session):
            return mock_block_repo

        monkeypatch.setattr("resalelens.services.fair_value.BlockRepository", mock_block_repo_init)

        request = FairValueRequest(
            block="123",
            street="ANG MO KIO AVE 3",
            flat_type="4 ROOM",
            floor_area_sqm=90.0,
            storey_range="04 TO 06",
            time_window_months=12,
        )

        comps, tier = select_comps(request, Mock())

        assert len(comps) == 10
        assert "same_block" in tier
