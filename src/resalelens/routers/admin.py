"""Admin API endpoints for manual data ingestion triggers and monitoring."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..ingestion.block_pois import ingest_block_pois
from ..ingestion.hdb_blocks import ingest_hdb_blocks
from ..ingestion.hdb_property_info import ingest_hdb_property_info
from ..ingestion.hdb_transactions import ingest_hdb_transactions
from ..ingestion.pois import ingest_pois

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db() -> Generator[Session, None, None]:
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/ingestion/trigger")
async def trigger_ingestion(
    dataset: str = Query(
        "hdb_transactions", description="Dataset to ingest (hdb_transactions, hdb_blocks, hdb_property_info, pois, or block_pois)"
    ),
    incremental: bool = Query(
        False, description="If True, only fetch new records since last run (for hdb_transactions)"
    ),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, int] | str]:
    """
    Manually trigger data ingestion for a specific dataset.

    Args:
        dataset: Dataset name to ingest (hdb_transactions or hdb_blocks)
        incremental: For hdb_transactions, only fetch records newer than latest in DB
        db: Database session

    Returns:
        Ingestion summary with status and statistics

    Raises:
        HTTPException 400: If invalid dataset name
        HTTPException 500: If ingestion fails
    """
    try:
        if dataset == "hdb_transactions":
            print(f"Triggering HDB transactions ingestion (incremental={incremental})...")
            summary = ingest_hdb_transactions(db, incremental=incremental)
            return {
                "status": "success",
                "dataset": dataset,
                "summary": summary,
            }
        elif dataset == "hdb_blocks":
            print("Triggering HDB blocks ingestion...")
            summary = ingest_hdb_blocks(db)
            return {
                "status": "success",
                "dataset": dataset,
                "summary": summary,
            }
        elif dataset == "hdb_property_info":
            print("Triggering HDB property information ingestion...")
            summary = ingest_hdb_property_info(db)
            return {
                "status": "success",
                "dataset": dataset,
                "summary": summary,
            }
        elif dataset == "pois":
            print("Triggering POI ingestion (MRT, LRT, supermarkets, clinics, parks, malls, hawkers, schools)...")
            summary = ingest_pois(db)
            return {
                "status": "success",
                "dataset": dataset,
                "summary": summary,
            }
        elif dataset == "block_pois":
            print("Triggering block-POI distance calculation...")
            summary = ingest_block_pois(db)
            return {
                "status": "success",
                "dataset": dataset,
                "summary": summary,
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid dataset: {dataset}. Must be 'hdb_transactions', 'hdb_blocks', 'hdb_property_info', 'pois', or 'block_pois'",
            )

    except ValueError as e:
        # Configuration error
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Ingestion failure
        print(f"Ingestion failed for {dataset}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        ) from e
