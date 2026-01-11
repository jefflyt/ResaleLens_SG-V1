"""Geospatial utilities for distance calculations."""

import math


def calculate_haversine_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate distance between two points using Haversine formula.

    The Haversine formula calculates the great-circle distance between two points
    on a sphere given their longitudes and latitudes. This is accurate for distances
    up to a few hundred kilometers.

    Args:
        lat1: Latitude of point 1 in decimal degrees
        lng1: Longitude of point 1 in decimal degrees
        lat2: Latitude of point 2 in decimal degrees
        lng2: Longitude of point 2 in decimal degrees

    Returns:
        Distance between the two points in meters

    Examples:
        >>> # Ang Mo Kio MRT to Bishan MRT (~2.5km)
        >>> dist = calculate_haversine_distance(1.3700, 103.8494, 1.3509, 103.8484)
        >>> assert 2400 < dist < 2600

        >>> # Same location
        >>> dist = calculate_haversine_distance(1.3521, 103.8198, 1.3521, 103.8198)
        >>> assert dist == 0.0

    References:
        https://en.wikipedia.org/wiki/Haversine_formula
    """
    # Earth's radius in meters (mean radius)
    EARTH_RADIUS_M = 6371000

    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_m = EARTH_RADIUS_M * c

    return distance_m
