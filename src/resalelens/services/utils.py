"""Utility functions for Fair Value calculation."""

import math
from datetime import date, timedelta

import pandas as pd


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two lat/lng points using Haversine formula.

    Args:
        lat1: Latitude of first point
        lng1: Longitude of first point
        lat2: Latitude of second point
        lng2: Longitude of second point

    Returns:
        Distance in meters
    """
    # Earth radius in meters
    R = 6371000

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(
        delta_lng / 2
    ) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def filter_by_date(transactions: list, months_back: int) -> list:
    """
    Filter transactions by time window.

    Args:
        transactions: List of Transaction ORM objects
        months_back: Number of months to look back

    Returns:
        Filtered list of transactions
    """
    cutoff_date = date.today() - timedelta(days=months_back * 30)
    return [t for t in transactions if t.date >= cutoff_date]


def parse_storey_range(storey_str: str) -> int:
    """
    Parse storey range string to get midpoint.

    Args:
        storey_str: Storey range string (e.g., "04 TO 06")

    Returns:
        Midpoint of storey range as integer

    Raises:
        ValueError: If storey range cannot be parsed
    """
    try:
        # Handle format "XX TO YY"
        parts = storey_str.strip().split(" TO ")
        if len(parts) == 2:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            return (low + high) // 2
        # Try single number (edge case)
        return int(storey_str.strip())
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Cannot parse storey range: {storey_str}") from e


def calculate_median_by_storey(df: pd.DataFrame) -> dict[int, float]:
    """
    Calculate median psm by storey tier.

    Args:
        df: DataFrame with 'storey_midpoint' and 'psm' columns

    Returns:
        Dictionary mapping storey tier to median psm
    """
    if df.empty or "storey_midpoint" not in df.columns or "psm" not in df.columns:
        return {}

    # Group by storey midpoint and calculate median psm
    storey_medians = df.groupby("storey_midpoint")["psm"].median().to_dict()
    return storey_medians
