"""Health check endpoints for monitoring."""

from time import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    """
    Check database health and connectivity.

    Returns database status, connection pool info, and response latency.
    Useful for monitoring and alerting in production.
    """
    start = time()

    try:
        # Simple query to test connection
        db.execute(text("SELECT 1"))
        latency_ms = (time() - start) * 1000

        # Get connection pool stats
        pool = db.bind.pool  # type: ignore[union-attr]

        return {
            "status": "healthy",
            "database": "postgresql",
            "latency_ms": round(latency_ms, 2),
            "connection_pool": {
                "size": pool.size(),  # type: ignore[union-attr]
                "checked_out": pool.checkedout(),  # type: ignore[union-attr]
                "overflow": pool.overflow(),  # type: ignore[union-attr]
                "checked_in": pool.size() - pool.checkedout(),  # type: ignore[union-attr]
            },
        }
    except Exception as e:
        latency_ms = (time() - start) * 1000
        return {"status": "unhealthy", "error": str(e), "latency_ms": round(latency_ms, 2)}
