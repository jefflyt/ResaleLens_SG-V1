"""Pydantic schemas for postal code operations."""

from pydantic import BaseModel, Field


class BlockLookupRequest(BaseModel):
    """Request schema for block lookup by postal code."""

    postal_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit Singapore postal code",
    )


class BlockLookupResponse(BaseModel):
    """Response schema for successful block lookup."""

    block: str = Field(..., description="HDB block number")
    street: str = Field(..., description="Street name (normalized)")
    town: str = Field(..., description="Town name")
    postal_code: str = Field(..., description="Postal code")
    postal_sector: str | None = Field(None, description="Postal sector (first 2 digits)")

    class Config:
        """Pydantic config."""

        from_attributes = True


class BlockMatch(BaseModel):
    """Individual block match for multiple results."""

    block: str
    street: str
    town: str
    postal_code: str
    postal_sector: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class BlockLookupMultipleResponse(BaseModel):
    """Response schema when multiple blocks match."""

    matches: list[BlockMatch] = Field(..., description="List of matching blocks")
    suggestions: bool = Field(
        True, description="Indicates these are multiple matches requiring user selection"
    )


class BlockLookupErrorResponse(BaseModel):
    """Response schema for lookup errors with suggestions."""

    error: str = Field(..., description="Error message")
    suggestions: list[BlockMatch] = Field(
        default_factory=list, description="Suggested blocks from same postal sector"
    )
