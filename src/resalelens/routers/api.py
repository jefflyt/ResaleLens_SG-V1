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
from ..schemas.fair_value import FairValueRequest, FairValueResponse
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
