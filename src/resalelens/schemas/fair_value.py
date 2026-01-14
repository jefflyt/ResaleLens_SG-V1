"""Pydantic schemas for Fair Value calculation."""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class FairValueRequest(BaseModel):
    """Request model for Fair Value calculation."""

    block: str = Field(..., description="Block number (e.g., '123')")
    street: str = Field(..., description="Street name")
    flat_type: str = Field(..., description="Flat type (e.g., '4 ROOM')")
    floor_area_sqm: float = Field(..., gt=0, lt=300, description="Floor area in square meters")
    storey_range: str = Field(..., description="Storey range (e.g., '04 TO 06')")
    time_window_months: int = Field(
        default=12, ge=1, le=60, description="Time window in months (max 5 years)"
    )
    user_asking_price: float | None = Field(
        default=None, gt=0, description="Optional user asking price for label assignment"
    )

    @field_validator("flat_type")
    @classmethod
    def validate_flat_type(cls, v: str) -> str:
        """Validate flat type is in expected format."""
        valid_types = {
            "1 ROOM",
            "2 ROOM",
            "3 ROOM",
            "4 ROOM",
            "5 ROOM",
            "EXECUTIVE",
            "MULTI-GENERATION",
        }
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid flat_type. Must be one of: {valid_types}")
        return v_upper


class Comp(BaseModel):
    """Comparable transaction model."""

    model_config = {"from_attributes": True}

    transaction_date: date = Field(..., description="Transaction date", alias="date")
    price: float = Field(..., description="Transaction price")
    psm: float = Field(..., description="Price per square meter")
    storey_range: str = Field(..., description="Storey range")
    distance_m: float = Field(..., description="Distance from target block in meters")
    flat_model: str = Field(..., description="HDB flat model")


class Explainability(BaseModel):
    """Explainability details for Fair Value calculation."""

    filters_applied: dict = Field(..., description="Filters used in comp selection")
    adjustments_made: dict = Field(..., description="Adjustments applied to comps")
    fallback_used: str = Field(..., description="Comp selection tier used")
    comp_count_before_outliers: int = Field(..., description="Comp count before outlier removal")
    comp_count_after_outliers: int = Field(..., description="Comp count after outlier removal")
    variance_cv: float = Field(..., description="Coefficient of variation of psm")
    median_comp_age_days: int = Field(..., description="Median age of comps in days")


class FairValueResponse(BaseModel):
    """Response model for Fair Value calculation."""

    fair_value_low: float = Field(..., description="Fair Value lower bound (P25)")
    fair_value_mid: float = Field(..., description="Fair Value midpoint")
    fair_value_high: float = Field(..., description="Fair Value upper bound (P75)")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    user_label: str | None = Field(
        default=None, description="User-facing label (Fair, Slightly high/low, etc.)"
    )
    comp_count: int = Field(..., description="Number of comps used in calculation")
    explainability: Explainability = Field(..., description="Explainability details")
    comps: list[Comp] = Field(..., description="List of comparable transactions")
