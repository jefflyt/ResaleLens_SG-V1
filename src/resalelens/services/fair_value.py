"""Fair Value calculation service.

This module implements the core Fair Value calculation engine with:
- Multi-tier comp selection ladder with automatic fallback
- Price-per-sqm normalization with storey adjustments
- Statistical outlier removal (percentile or MAD methods)
- Confidence scoring based on comp count, variance, and recency
- Full explainability output
"""

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from ..data.repositories import BlockRepository, TransactionRepository
from ..models import Transaction
from ..schemas.fair_value import Comp, Explainability, FairValueRequest, FairValueResponse
from .utils import calculate_median_by_storey, haversine_distance, parse_storey_range

# Configuration constants (can be moved to env vars later)
MIN_COMPS_THRESHOLD = 5
RADIUS_M = 500
DEFAULT_OUTLIER_METHOD = "percentile"


def select_comps(request: FairValueRequest, db: Session) -> tuple[list[Transaction], str]:
    """
    Select comparable transactions using 4-tier fallback ladder.

    Tier 1: Same block + flat_type (12 months)
    Tier 2: Same block + flat_type (24 months)
    Tier 3: Nearby radius (500m) + town + flat_type (12/24 months)
    Tier 4: Town-level + flat_type (12/24 months)

    Args:
        request: Fair Value request parameters
        db: Database session

    Returns:
        Tuple of (comps list, fallback tier used)
    """
    repo = TransactionRepository(db)

    # Tier 1: Same block, 12 months
    comps = repo.get_transactions_by_block(
        request.block, request.street, request.flat_type, request.time_window_months
    )
    if len(comps) >= MIN_COMPS_THRESHOLD:
        tier = f"same_block_{request.time_window_months}m"
        return (comps, tier)

    # Tier 2: Same block, 24 months
    if request.time_window_months < 24:
        comps = repo.get_transactions_by_block(request.block, request.street, request.flat_type, 24)
        if len(comps) >= MIN_COMPS_THRESHOLD:
            return (comps, "same_block_24m")

    # Tier 3: Nearby radius (need block lat/lng first)
    block_repo = BlockRepository(db)
    block = block_repo.get_by_block_and_street(request.block, request.street)

    if block and block.latitude and block.longitude:
        town = block.town
        lat = float(block.latitude)
        lng = float(block.longitude)

        # Try with request time window first
        comps = repo.get_transactions_by_radius(
            lat, lng, RADIUS_M, town, request.flat_type, request.time_window_months
        )
        if len(comps) >= MIN_COMPS_THRESHOLD:
            tier = f"nearby_{RADIUS_M}m_{request.time_window_months}m"
            return (comps, tier)

        # Try 24 months if not already
        if request.time_window_months < 24:
            comps = repo.get_transactions_by_radius(
                lat, lng, RADIUS_M, town, request.flat_type, 24
            )
            if len(comps) >= MIN_COMPS_THRESHOLD:
                return (comps, f"nearby_{RADIUS_M}m_24m")

    # Tier 4: Town-level
    # Get town from block or fallback to querying a transaction
    town = block.town if block else None
    if not town:
        # Fallback: try to get town from any transaction for this block
        sample_txns = repo.get_transactions_by_block(request.block, request.street, "", 60)
        if sample_txns:
            town = sample_txns[0].town

    if town:
        # Try with request time window first
        comps = repo.get_transactions_by_town(town, request.flat_type, request.time_window_months)
        if len(comps) >= MIN_COMPS_THRESHOLD:
            tier = f"town_{request.time_window_months}m"
            return (comps, tier)

        # Try 24 months
        if request.time_window_months < 24:
            comps = repo.get_transactions_by_town(town, request.flat_type, 24)
            if len(comps) >= MIN_COMPS_THRESHOLD:
                return (comps, "town_24m")

        # Return whatever we have at town level
        return (comps, "town_insufficient")

    # Exhausted all tiers
    return (comps, "insufficient_data")


def normalize_comps(
    comps: list[Transaction], user_storey_range: str, user_block_lat: float | None = None, user_block_lng: float | None = None
) -> pd.DataFrame:
    """
    Normalize comparable transactions with psm and storey adjustments.

    Args:
        comps: List of comparable transactions
        user_storey_range: User's storey range (e.g., "04 TO 06")
        user_block_lat: User's block latitude (for distance calculation)
        user_block_lng: User's block longitude (for distance calculation)

    Returns:
        DataFrame with normalized comps
    """
    if not comps:
        return pd.DataFrame()

    # Convert to DataFrame
    records = []
    for t in comps:
        records.append(
            {
                "date": t.date,
                "price": float(t.price),
                "floor_area_sqm": float(t.floor_area_sqm),
                "storey_range": t.storey_range,
                "flat_model": t.flat_model,
                "latitude": float(t.latitude) if t.latitude else None,
                "longitude": float(t.longitude) if t.longitude else None,
            }
        )
    df = pd.DataFrame(records)

    # Calculate base psm
    df["psm"] = df["price"] / df["floor_area_sqm"]

    # Parse storey ranges
    df["storey_midpoint"] = df["storey_range"].apply(
        lambda x: parse_storey_range(x) if pd.notna(x) else None
    )

    # Calculate distance from user block (if lat/lng available)
    if user_block_lat and user_block_lng:
        df["distance_m"] = df.apply(
            lambda row: (
                haversine_distance(
                    user_block_lat, user_block_lng, row["latitude"], row["longitude"]
                )
                if pd.notna(row["latitude"]) and pd.notna(row["longitude"])
                else 0.0
            ),
            axis=1,
        )
    else:
        df["distance_m"] = 0.0

    # Storey adjustment (if we have enough data)
    try:
        user_storey_midpoint = parse_storey_range(user_storey_range)
        storey_medians = calculate_median_by_storey(df)

        if storey_medians and user_storey_midpoint in storey_medians:
            user_baseline = storey_medians[user_storey_midpoint]

            def adjust_for_storey(row: Any) -> float:
                comp_storey = row["storey_midpoint"]
                comp_psm = row["psm"]
                if pd.notna(comp_storey) and comp_storey in storey_medians:
                    comp_baseline = storey_medians[comp_storey]
                    if comp_baseline > 0:
                        adjustment_factor = user_baseline / comp_baseline
                        return comp_psm * adjustment_factor
                return comp_psm

            df["adjusted_psm"] = df.apply(adjust_for_storey, axis=1)
        else:
            # Not enough storey data, use unadjusted psm
            df["adjusted_psm"] = df["psm"]
    except (ValueError, KeyError):
        # Storey parsing failed, use unadjusted psm
        df["adjusted_psm"] = df["psm"]

    return df


def remove_outliers(df: pd.DataFrame, method: str = DEFAULT_OUTLIER_METHOD) -> pd.DataFrame:
    """
    Remove statistical outliers from comps.

    Args:
        df: DataFrame with comps
        method: Outlier removal method ("percentile" or "mad")

    Returns:
        DataFrame with outliers removed
    """
    if df.empty or len(df) < 3:
        # Not enough data for outlier removal
        return df

    if method == "percentile":
        # P5-P95 method
        p5 = df["adjusted_psm"].quantile(0.05)
        p95 = df["adjusted_psm"].quantile(0.95)
        filtered = df[(df["adjusted_psm"] >= p5) & (df["adjusted_psm"] <= p95)]
        return filtered

    elif method == "mad":
        # MAD (Median Absolute Deviation) method
        median = df["adjusted_psm"].median()
        mad = (df["adjusted_psm"] - median).abs().median()
        if mad == 0:
            # All values are identical, no outliers
            return df
        threshold = 2.5 * mad
        filtered = df[(df["adjusted_psm"] - median).abs() <= threshold]
        return filtered

    # Default: return as-is
    return df


def calculate_confidence(df: pd.DataFrame, time_window_months: int) -> int:
    """
    Calculate confidence score (0-100) based on comp count, variance, and recency.

    Args:
        df: DataFrame with comps
        time_window_months: Time window used for comp selection

    Returns:
        Confidence score (0-100)
    """
    score = 0

    # Component 1: Comp count (max 40 points)
    n = len(df)
    if n >= 20:
        score += 40
    elif n >= 10:
        score += 30
    elif n >= 5:
        score += 20
    else:
        score += 10

    # Component 2: Variance (max 30 points)
    if n > 1:
        mean_psm = df["adjusted_psm"].mean()
        std_psm = df["adjusted_psm"].std()
        cv = std_psm / mean_psm if mean_psm > 0 else 1.0

        if cv < 0.10:
            score += 30
        elif cv < 0.20:
            score += 20
        else:
            score += 10
    else:
        score += 5

    # Component 3: Recency (max 30 points)
    if not df.empty:
        today = date.today()
        df["age_days"] = df["date"].apply(lambda d: (today - d).days)
        median_age = df["age_days"].median()

        if median_age < 90:  # < 3 months
            score += 30
        elif median_age < 180:  # 3-6 months
            score += 20
        elif median_age < 365:  # 6-12 months
            score += 10
        else:
            score += 5

    return min(score, 100)


def generate_fair_value_band(df: pd.DataFrame, user_floor_area: float) -> tuple[float, float, float]:
    """
    Generate Fair Value band (P25-P75) from normalized comps.

    Args:
        df: DataFrame with normalized comps
        user_floor_area: User's floor area in sqm

    Returns:
        Tuple of (low, mid, high) Fair Value prices
    """
    if df.empty:
        return (0.0, 0.0, 0.0)

    p25_psm = df["adjusted_psm"].quantile(0.25)
    p75_psm = df["adjusted_psm"].quantile(0.75)
    median_psm = df["adjusted_psm"].median()

    low = p25_psm * user_floor_area
    high = p75_psm * user_floor_area
    mid = median_psm * user_floor_area

    return (float(low), float(mid), float(high))


def assign_user_label(
    user_asking_price: float | None, fair_value_low: float, fair_value_high: float, confidence: int
) -> str:
    """
    Assign user-facing label based on asking price relative to Fair Value band.

    Args:
        user_asking_price: User's asking price (optional)
        fair_value_low: Fair Value lower bound
        fair_value_high: Fair Value upper bound
        confidence: Confidence score

    Returns:
        User label string
    """
    # Check for insufficient data first
    if confidence < 20:
        return "Insufficient data"

    # If no asking price, return neutral label
    if user_asking_price is None:
        return "Fair Value calculated"

    # Calculate tolerance (10% of band edges)
    low_tolerance = fair_value_low * 0.10
    high_tolerance = fair_value_high * 0.10

    # Assign label
    if fair_value_low <= user_asking_price <= fair_value_high:
        return "Fair"
    elif user_asking_price < fair_value_low:
        if (fair_value_low - user_asking_price) <= low_tolerance:
            return "Slightly low"
        else:
            return "High risk (too low)"
    else:  # user_asking_price > fair_value_high
        if (user_asking_price - fair_value_high) <= high_tolerance:
            return "Slightly high"
        else:
            return "High risk (too high)"


def build_explainability(
    df: pd.DataFrame,
    df_before_outliers: pd.DataFrame,
    fallback_tier: str,
    request: FairValueRequest,
) -> Explainability:
    """
    Build explainability output for Fair Value calculation.

    Args:
        df: DataFrame after outlier removal
        df_before_outliers: DataFrame before outlier removal
        fallback_tier: Comp selection tier used
        request: Original request

    Returns:
        Explainability object
    """
    today = date.today()

    filters_applied = {
        "block": request.block,
        "street": request.street,
        "flat_type": request.flat_type,
        "time_window_months": request.time_window_months,
    }
    if "nearby" in fallback_tier:
        filters_applied["radius_m"] = RADIUS_M

    adjustments_made = {
        "storey_adjustment": "Applied" if "storey_midpoint" in df.columns else "Not applied",
        "outlier_removal_method": DEFAULT_OUTLIER_METHOD,
    }

    variance_cv = 0.0
    if len(df) > 1:
        mean_psm = df["adjusted_psm"].mean()
        std_psm = df["adjusted_psm"].std()
        variance_cv = float(std_psm / mean_psm) if mean_psm > 0 else 0.0

    median_comp_age_days = 0
    if not df.empty:
        df["age_days"] = df["date"].apply(lambda d: (today - d).days)
        median_comp_age_days = int(df["age_days"].median())

    return Explainability(
        filters_applied=filters_applied,
        adjustments_made=adjustments_made,
        fallback_used=fallback_tier,
        comp_count_before_outliers=len(df_before_outliers),
        comp_count_after_outliers=len(df),
        variance_cv=variance_cv,
        median_comp_age_days=median_comp_age_days,
    )


def calculate_fair_value(request: FairValueRequest, db: Session) -> FairValueResponse:
    """
    Main entry point for Fair Value calculation.

    Orchestrates the entire calculation pipeline:
    1. Select comps using fallback ladder
    2. Normalize comps (psm + storey adjustments)
    3. Remove outliers
    4. Calculate confidence score
    5. Generate Fair Value band
    6. Assign user label
    7. Build explainability output

    Args:
        request: Fair Value request parameters
        db: Database session

    Returns:
        Fair Value response with band, confidence, comps, and explainability
    """
    # Step 1: Select comps
    comps, fallback_tier = select_comps(request, db)

    # Get block lat/lng for distance calculations
    block_repo = BlockRepository(db)
    block = block_repo.get_by_block_and_street(request.block, request.street)
    user_lat = float(block.latitude) if block and block.latitude else None
    user_lng = float(block.longitude) if block and block.longitude else None

    # Step 2: Normalize comps
    df = normalize_comps(comps, request.storey_range, user_lat, user_lng)
    df_before_outliers = df.copy()

    # Step 3: Remove outliers
    df = remove_outliers(df, DEFAULT_OUTLIER_METHOD)

    # Step 4: Calculate confidence
    confidence = calculate_confidence(df, request.time_window_months)

    # Step 5: Generate Fair Value band
    fair_value_low, fair_value_mid, fair_value_high = generate_fair_value_band(
        df, request.floor_area_sqm
    )

    # Step 6: Assign user label
    user_label = assign_user_label(
        request.user_asking_price, fair_value_low, fair_value_high, confidence
    )

    # Step 7: Build explainability
    explainability = build_explainability(df, df_before_outliers, fallback_tier, request)

    # Step 8: Build comp list for response
    comp_list = []
    for _, row in df.iterrows():
        comp_list.append(
            Comp(
                date=row["date"],  # Use alias name
                price=row["price"],
                psm=row["psm"],
                storey_range=row["storey_range"],
                distance_m=row["distance_m"],
                flat_model=row["flat_model"],
            )
        )

    return FairValueResponse(
        fair_value_low=fair_value_low,
        fair_value_mid=fair_value_mid,
        fair_value_high=fair_value_high,
        confidence_score=confidence,
        user_label=user_label,
        comp_count=len(df),
        explainability=explainability,
        comps=comp_list,
    )
