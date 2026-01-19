"""Schemas for Block X-Ray feature."""

from datetime import datetime

from pydantic import BaseModel


class POIDistance(BaseModel):
    """POI with distance information."""

    name: str
    poi_type: str
    distance_m: float


class BlockFacilities(BaseModel):
    """Block facility flags."""

    commercial: bool
    market_hawker: bool
    multistorey_carpark: bool
    precinct_pavilion: bool


class UnitCompositionItem(BaseModel):
    """Unit composition breakdown item (sold + rental units)."""

    room_type: str
    sold_units: int
    rental_units: int
    total_units: int
    percentage: float


class TrendDataPoint(BaseModel):
    """Transaction trend data point for a specific quarter."""

    quarter: str  # Format: "Q1 2023", "Q2 2024", etc.
    median_psm: float  # Median price per square meter for the quarter


class VolatilityInfo(BaseModel):
    """Price volatility information."""

    std_dev: float  # Standard deviation of PSM
    classification: str  # "low", "medium", "high"
    label: str  # "Stable Market", "Moderate Fluctuation", "High Volatility"


class BlockXRayData(BaseModel):
    """Complete Block X-Ray data response."""

    # Block identification
    block_id: int
    block: str
    street: str
    town: str
    postal_code: str | None

    # Building characteristics
    lease_commence_year: int | None
    remaining_lease_years: int | None
    building_age: int | None
    max_floor_lvl: int | None
    year_completed: int | None
    total_dwelling_units: int | None

    # Facilities
    facilities: BlockFacilities

    # Nearby amenities (within 500m)
    nearby_amenities: list[POIDistance]

    # Unit composition (sold + rental units)
    unit_composition: list[UnitCompositionItem]

    # Transaction analytics (past 2 years)
    transaction_trends: list[TrendDataPoint]
    volatility: VolatilityInfo | None

    # Metadata
    last_updated: datetime | None

