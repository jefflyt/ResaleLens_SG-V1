"""[DEPRECATED] HDB blocks ingestion with geocoding - use hdb_postal_codes.py instead."""

from __future__ import annotations

from sqlalchemy.orm import Session

# This module is deprecated - use hdb_postal_codes.py for postal code ingestion


def ingest_hdb_blocks(
    session: Session, batch_size: int | None = None, skip_existing: bool = True
) -> dict[str, int]:
    """
    [DEPRECATED] HDB blocks ingestion using OneMap geocoding.

    This function has been deprecated. Use ingest_hdb_postal_codes() from
    hdb_postal_codes.py instead, which uses pattern-based postal code
    generation without external API calls.

    Args:
        session: Database session
        batch_size: Optional limit on number of blocks to process
        skip_existing: If True, skip blocks that already have coordinates

    Returns:
        Dictionary with ingestion statistics

    Raises:
        NotImplementedError: This function is deprecated
    """
    raise NotImplementedError(
        "ingest_hdb_blocks() is deprecated. OneMap geocoding has been replaced "
        "with pattern-based postal code generation. Use ingest_hdb_postal_codes() "
        "from hdb_postal_codes.py instead."
    )
