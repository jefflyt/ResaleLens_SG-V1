"""Admin API endpoints for manual data ingestion triggers and monitoring."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..ingestion import ingest_hdb_blocks, ingest_hdb_transactions

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
        "hdb_transactions", description="Dataset to ingest (hdb_transactions or hdb_blocks)"
    ),
    db: Session = Depends(get_db),
) -> dict[str, dict[str, int] | str]:
    """
    Manually trigger data ingestion for a specific dataset.

    Args:
        dataset: Dataset name to ingest (hdb_transactions or hdb_blocks)
        db: Database session

    Returns:
        Ingestion summary with status and statistics

    Raises:
        HTTPException 400: If invalid dataset name
        HTTPException 500: If ingestion fails
    """
    try:
        if dataset == "hdb_transactions":
            print("Triggering HDB transactions ingestion...")
            summary = ingest_hdb_transactions(db)
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
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid dataset: {dataset}. Must be 'hdb_transactions' or 'hdb_blocks'",
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
