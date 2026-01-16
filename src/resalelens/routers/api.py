"""Public API endpoints for Fair Value and other services."""

from collections.abc import Generator
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..ingestion.utils import normalize_street_name
from ..models import IngestionRun, IngestionStatus
from ..schemas.block_xray import BlockXRayData
from ..schemas.fair_value import FairValueRequest, FairValueResponse
from ..services.block_xray import get_block_xray
from ..services.data_status import get_data_status
from ..services.fair_value import calculate_fair_value

router = APIRouter(prefix="/api", tags=["api"])

# Configure Jinja2 templates
templates_path = Path(__file__).parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


def get_db() -> Generator[Session, None, None]:
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_last_updated_timestamp(db: Session, dataset_name: str) -> datetime | None:
    """
    Get the timestamp of the most recent successful ingestion run for a dataset.

    Args:
        db: Database session
        dataset_name: Name of the dataset (e.g., "hdb_transactions")

    Returns:
        Datetime of last successful ingestion, or None if no successful runs found
    """
    last_run = (
        db.query(IngestionRun)
        .filter(
            IngestionRun.dataset_name == dataset_name,
            IngestionRun.status == IngestionStatus.SUCCESS,
        )
        .order_by(IngestionRun.completed_at.desc())
        .first()
    )

    return last_run.completed_at if last_run else None


@router.post("/fair-value", response_model=None)
async def calculate_fair_value_api(
    request: Request, db: Session = Depends(get_db)
) -> HTMLResponse | dict:
    """
    Calculate Fair Value for a given HDB unit.

    This endpoint accepts unit details (block, street, flat type, floor area, storey range)
    and returns a Fair Value assessment with:
    - Fair Value price band (P25-P75)
    - Confidence score (0-100)
    - User-facing label (Fair, Slightly high/low, High risk, etc.)
    - List of comparable transactions
    - Full explainability (filters, adjustments, fallback tier used)
    - Last updated timestamp for transaction data

    Supports both JSON and HTML responses:
    - HTMX requests (HX-Request header): Returns HTML fragment
    - Regular requests: Returns JSON

    Args:
        request: FastAPI request object
        db: Database session (injected)

    Returns:
        HTML response for HTMX or JSON dict for regular requests

    Raises:
        HTTPException 422: Validation error (handled by FastAPI/Pydantic)
        HTTPException 404: Block not found
        HTTPException 500: Fair Value calculation failed
    """
    try:
        # Parse form data
        form_data = await request.form()

        # Normalize user input to match database format
        # This allows users to enter addresses with abbreviations, lowercase, extra spaces, etc.
        block_input = form_data.get("block")
        street_input = form_data.get("street")
        flat_type_input = form_data.get("flat_type")
        floor_area_input = form_data.get("floor_area_sqm")
        storey_range_input = form_data.get("storey_range")
        time_window_input = form_data.get("time_window_months", "12")

        # Ensure we have string values (form_data.get returns UploadFile | str | None)
        block_str = str(block_input) if block_input else ""
        street_str = str(street_input) if street_input else ""
        flat_type_str = str(flat_type_input) if flat_type_input else ""
        floor_area_str = str(floor_area_input) if floor_area_input else "0"
        storey_range_str = str(storey_range_input) if storey_range_input else ""
        time_window_str = str(time_window_input) if time_window_input else "12"

        # Normalize block: uppercase and strip whitespace
        normalized_block = block_str.upper().strip()

        # Normalize street: expand abbreviations, uppercase, strip whitespace
        normalized_street = normalize_street_name(street_str)

        # Build Fair Value request with normalized inputs
        fv_request = FairValueRequest(
            block=normalized_block,
            street=normalized_street,
            flat_type=flat_type_str,
            floor_area_sqm=float(floor_area_str),
            storey_range=storey_range_str,
            time_window_months=int(time_window_str),
        )

        # Calculate Fair Value using service
        result: FairValueResponse = calculate_fair_value(fv_request, db)

        # Get last updated timestamp for transaction data
        last_updated = get_last_updated_timestamp(db, "hdb_transactions")

        # Check if this is an HTMX request
        is_htmx = request.headers.get("HX-Request") == "true"

        if is_htmx:
            # Return HTML fragment for HTMX
            return templates.TemplateResponse(
                request=request,
                name="results.html",
                context={
                    "request": request,
                    "fair_value_low": result.fair_value_low,
                    "fair_value_mid": result.fair_value_mid,
                    "fair_value_high": result.fair_value_high,
                    "confidence_score": result.confidence_score,
                    "user_label": result.user_label,
                    "comp_count": result.comp_count,
                    "floor_area_sqm": fv_request.floor_area_sqm,
                    "explainability": result.explainability,
                    "comps": [
                        {
                            "date": comp.transaction_date.isoformat(),
                            "price": comp.price,
                            "psm": comp.psm,
                            "storey_range": comp.storey_range,
                            "distance_m": comp.distance_m,
                            "flat_model": comp.flat_model,
                        }
                        for comp in result.comps
                    ],
                    "last_updated": (
                        last_updated.strftime("%Y-%m-%d %H:%M:%S") if last_updated else "N/A"
                    ),
                },
            )
        else:
            # Return JSON for regular API requests
            response = {
                "fair_value_low": result.fair_value_low,
                "fair_value_mid": result.fair_value_mid,
                "fair_value_high": result.fair_value_high,
                "confidence_score": result.confidence_score,
                "user_label": result.user_label,
                "comp_count": result.comp_count,
                "explainability": {
                    "filters_applied": result.explainability.filters_applied,
                    "adjustments_made": result.explainability.adjustments_made,
                    "fallback_used": result.explainability.fallback_used,
                    "comp_count_before_outliers": result.explainability.comp_count_before_outliers,
                    "comp_count_after_outliers": result.explainability.comp_count_after_outliers,
                    "variance_cv": result.explainability.variance_cv,
                    "median_comp_age_days": result.explainability.median_comp_age_days,
                },
                "comps": [
                    {
                        "date": comp.transaction_date.isoformat(),
                        "price": comp.price,
                        "psm": comp.psm,
                        "storey_range": comp.storey_range,
                        "distance_m": comp.distance_m,
                        "flat_model": comp.flat_model,
                    }
                    for comp in result.comps
                ],
                "last_updated": last_updated.isoformat() if last_updated else None,
            }

            return response

    except ValueError as e:
        # Block not found or validation error
        error_message = str(e)
        if "not found" in error_message.lower() or "invalid" in error_message.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Block not found. Please check your input: {error_message}",
            ) from e
        raise HTTPException(status_code=400, detail=error_message) from e

    except Exception as e:
        # Unexpected error during calculation
        print(f"Fair Value calculation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to calculate Fair Value. Please try again later.",
        ) from e


@router.get("/block-lookup")
async def block_lookup(
    postal_code: str, db: Session = Depends(get_db)
) -> dict:
    """
    Lookup HDB block information by postal code.

    This endpoint implements intelligent lookup strategies:
    1. **Direct match**: Exact postal code lookup in blocks table
    2. **HDB inference**: For postal codes starting with 6/7, infer block from last 3 digits
    3. **Sector fallback**: Search within same postal sector (first 2 digits) for suggestions

    Args:
        postal_code: 6-digit Singapore postal code
        db: Database session (injected)

    Returns:
        - Single match: {block, street, town, postal_code, postal_sector}
        - Multiple matches: {matches: [...], suggestions: true}
        - No match with suggestions: {error: "...", suggestions: [...]}

    Raises:
        HTTPException 400: Invalid postal code format
        HTTPException 404: Postal code not found and no suggestions available
    """
    from ..models import Block
    from ..schemas.postal_code import (
        BlockLookupErrorResponse,
        BlockLookupMultipleResponse,
        BlockLookupResponse,
        BlockMatch,
    )

    # Validate postal code format
    if not postal_code or len(postal_code) != 6 or not postal_code.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid postal code format. Please enter a 6-digit numeric postal code.",
        )

    # Extract postal sector (first 2 digits)
    postal_sector = postal_code[:2]

    # Strategy 1: Direct match - exact postal code lookup
    direct_matches = (
        db.query(Block)
        .filter(Block.postal_code == postal_code)
        .all()
    )

    if direct_matches:
        if len(direct_matches) == 1:
            # Single match - return immediately
            block = direct_matches[0]
            return BlockLookupResponse(
                block=block.block,
                street=block.street,
                town=block.town,
                postal_code=block.postal_code or postal_code,
                postal_sector=block.postal_sector,
            ).model_dump()
        else:
            # Multiple matches - user needs to select
            matches = [
                BlockMatch(
                    block=b.block,
                    street=b.street,
                    town=b.town,
                    postal_code=b.postal_code or postal_code,
                    postal_sector=b.postal_sector,
                )
                for b in direct_matches
            ]
            return BlockLookupMultipleResponse(
                matches=matches, suggestions=True
            ).model_dump()

    # Strategy 2: HDB block inference (last 3 digits = block number)
    # Only for HDB postal codes (starting with 6, 7, or 8)
    if postal_code.startswith(("6", "7", "8")):
        inferred_block = postal_code[-3:].lstrip("0") or "0"  # Remove leading zeros

        # Search for block in same postal sector
        inferred_matches = (
            db.query(Block)
            .filter(
                Block.block == inferred_block,
                Block.postal_sector == postal_sector,
            )
            .all()
        )

        if inferred_matches:
            if len(inferred_matches) == 1:
                block = inferred_matches[0]
                return BlockLookupResponse(
                    block=block.block,
                    street=block.street,
                    town=block.town,
                    postal_code=block.postal_code or postal_code,
                    postal_sector=block.postal_sector,
                ).model_dump()
            else:
                # Multiple inferred matches
                matches = [
                    BlockMatch(
                        block=b.block,
                        street=b.street,
                        town=b.town,
                        postal_code=b.postal_code or postal_code,
                        postal_sector=b.postal_sector,
                    )
                    for b in inferred_matches
                ]
                return BlockLookupMultipleResponse(
                    matches=matches, suggestions=True
                ).model_dump()

    # Strategy 3: Sector fallback - find blocks in same postal sector
    sector_blocks = (
        db.query(Block)
        .filter(Block.postal_sector == postal_sector)
        .limit(10)  # Limit to 10 suggestions
        .all()
    )

    if sector_blocks:
        # Return suggestions from same sector
        suggestions = [
            BlockMatch(
                block=b.block,
                street=b.street,
                town=b.town,
                postal_code=b.postal_code or "",
                postal_sector=b.postal_sector,
            )
            for b in sector_blocks
        ]
        return BlockLookupErrorResponse(
            error=(
                f"Postal code {postal_code} not found. "
                f"Here are some blocks in the same area (sector {postal_sector}):"
            ),
            suggestions=suggestions,
        ).model_dump()

    # No matches found at all
    raise HTTPException(
        status_code=404,
        detail=(
            f"Postal code {postal_code} not found in our database. "
            "Please use manual entry (block + street)."
        ),
    )


@router.get("/block-xray/{block_id}", response_model=BlockXRayData)
async def get_block_xray_api(block_id: int, db: Session = Depends(get_db)) -> BlockXRayData:
    """
    Get Block X-Ray data including property information.

    Args:
        block_id: Block ID to query
        db: Database session

    Returns:
        BlockXRayData with building characteristics, facilities, and amenities

    Raises:
        HTTPException 404: Block not found
    """
    block_data = get_block_xray(block_id, db)

    if not block_data:
        raise HTTPException(status_code=404, detail="Block not found")

    return block_data


@router.get("/block/{block_id}")
async def block_xray_page(
    request: Request, block_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Render Block X-Ray page with property information.

    Args:
        request: FastAPI request object
        block_id: Block ID to display
        db: Database session

    Returns:
        Rendered template

    Raises:
        HTTPException 404: Block not found
    """
    block_data = get_block_xray(block_id, db)

    if not block_data:
        raise HTTPException(status_code=404, detail="Block not found")

    return templates.TemplateResponse(
        "block_xray.html",
        {
            "request": request,
            "block": block_data,
        },
    )


@router.get("/data-status")
async def data_status_page(
    request: Request, db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Render Data Status page showing dataset freshness and ingestion health.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Rendered template with dataset status information
    """
    datasets = get_data_status(db)

    return templates.TemplateResponse(
        request=request,
        name="data_status.html",
        context={
            "request": request,
            "datasets": datasets,
        },
    )


@router.get("/api/data-status")
async def data_status_json(
    db: Session = Depends(get_db)
) -> dict:
    """
    Get data status as JSON for all tracked datasets.

    Returns:
        Dictionary with 'datasets' key containing list of DatasetStatus objects
    """
    datasets = get_data_status(db)
    return {"datasets": [d.model_dump() for d in datasets]}
