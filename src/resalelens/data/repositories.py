"""Repository pattern implementation for data access."""

from datetime import date
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models import (
    POI,
    Block,
    BlockPOI,
    IngestionRun,
    Lead,
    LeadStatus,
    POIType,
    Transaction,
)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: Session, model: type[T]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
            model: Model class for this repository
        """
        self.session = session
        self.model_class = model

    def get_by_id(self, id: int) -> T | None:
        """Get entity by ID."""
        return self.session.get(self.model_class, id)

    def create(self, **kwargs: Any) -> T:
        """Create a new entity."""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity."""
        self.session.delete(entity)
        self.session.commit()

    def get_all(self, limit: int | None = None, offset: int = 0) -> list[T]:
        """Get all entities with optional pagination."""
        query = select(self.model_class).offset(offset)
        if limit:
            query = query.limit(limit)
        result = self.session.execute(query)
        return list(result.scalars().all())


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction model with custom queries."""

    def __init__(self, session: Session):
        """Initialize TransactionRepository."""
        super().__init__(session, Transaction)

    def get_by_block_and_date_range(
        self, block: str, street: str, start_date: date, end_date: date
    ) -> list[Transaction]:
        """
        Get transactions for a specific block within a date range.

        Args:
            block: Block number
            street: Street name
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of transactions
        """
        query = select(Transaction).where(
            and_(
                Transaction.block == block,
                Transaction.street == street,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        )
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_by_town_and_flat_type(
        self, town: str, flat_type: str, start_date: date, end_date: date
    ) -> list[Transaction]:
        """
        Get transactions for a town and flat type within a date range.

        Args:
            town: Town name
            flat_type: Flat type (e.g., "3 ROOM", "4 ROOM")
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of transactions
        """
        query = select(Transaction).where(
            and_(
                Transaction.town == town,
                Transaction.flat_type == flat_type,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        )
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_within_radius(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        flat_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Transaction]:
        """
        Get transactions within a radius of a point.

        Uses Haversine formula approximation for distance calculation.
        Note: For production, consider using PostGIS for more accurate geo queries.

        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Radius in kilometers
            flat_type: Optional flat type filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of transactions within radius
        """
        # Haversine formula approximation
        # Distance in km ≈ sqrt((lat2-lat1)^2 + (lon2-lon1)^2) * 111.32
        lat_delta = radius_km / 111.32
        lon_delta = radius_km / (111.32 * func.cos(func.radians(latitude)))

        conditions: list[Any] = [
            Transaction.latitude.isnot(None),
            Transaction.longitude.isnot(None),
            Transaction.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Transaction.longitude.between(longitude - lon_delta, longitude + lon_delta),
        ]

        if flat_type:
            conditions.append(Transaction.flat_type == flat_type)
        if start_date:
            conditions.append(Transaction.date >= start_date)
        if end_date:
            conditions.append(Transaction.date <= end_date)

        query = select(Transaction).where(and_(*conditions))
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_transactions_by_block(
        self, block: str, street: str, flat_type: str, months_back: int
    ) -> list[Transaction]:
        """
        Get transactions for a specific block, flat type, and time window.

        Args:
            block: Block number
            street: Street name
            flat_type: Flat type (e.g., "4 ROOM")
            months_back: Number of months to look back

        Returns:
            List of transactions
        """
        from datetime import date, timedelta

        cutoff_date = date.today() - timedelta(days=months_back * 30)
        query = select(Transaction).where(
            and_(
                Transaction.block == block,
                Transaction.street == street,
                Transaction.flat_type == flat_type,
                Transaction.date >= cutoff_date,
            )
        )
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_transactions_by_radius(
        self,
        lat: float,
        lng: float,
        radius_m: float,
        town: str,
        flat_type: str,
        months_back: int,
    ) -> list[Transaction]:
        """
        Get transactions within a radius of a point, filtered by town and flat type.

        Uses bounding box pre-filter then Haversine post-filter for accuracy.

        Args:
            lat: Center point latitude
            lng: Center point longitude
            radius_m: Radius in meters
            town: Town name
            flat_type: Flat type
            months_back: Number of months to look back

        Returns:
            List of transactions within radius
        """
        from datetime import date, timedelta

        from ..services.utils import haversine_distance

        cutoff_date = date.today() - timedelta(days=months_back * 30)
        radius_km = radius_m / 1000.0

        # Bounding box approximation for DB query
        lat_delta = radius_km / 111.32
        lon_delta = radius_km / (111.32 * func.cos(func.radians(lat)))

        query = select(Transaction).where(
            and_(
                Transaction.town == town,
                Transaction.flat_type == flat_type,
                Transaction.date >= cutoff_date,
                Transaction.latitude.isnot(None),
                Transaction.longitude.isnot(None),
                Transaction.latitude.between(lat - lat_delta, lat + lat_delta),
                Transaction.longitude.between(lng - lon_delta, lng + lon_delta),
            )
        )
        result = self.session.execute(query)
        candidates = list(result.scalars().all())

        # Post-filter with accurate Haversine distance
        filtered = []
        for t in candidates:
            if t.latitude is not None and t.longitude is not None:
                dist = haversine_distance(lat, lng, float(t.latitude), float(t.longitude))
                if dist <= radius_m:
                    filtered.append(t)

        return filtered

    def get_transactions_by_town(
        self, town: str, flat_type: str, months_back: int
    ) -> list[Transaction]:
        """
        Get transactions for a town, flat type, and time window.

        Args:
            town: Town name
            flat_type: Flat type
            months_back: Number of months to look back

        Returns:
            List of transactions
        """
        from datetime import date, timedelta

        cutoff_date = date.today() - timedelta(days=months_back * 30)
        query = select(Transaction).where(
            and_(
                Transaction.town == town,
                Transaction.flat_type == flat_type,
                Transaction.date >= cutoff_date,
            )
        )
        result = self.session.execute(query)
        return list(result.scalars().all())


class BlockRepository(BaseRepository[Block]):
    """Repository for Block model with custom queries."""

    def __init__(self, session: Session):
        """Initialize BlockRepository."""
        super().__init__(session, Block)

    def get_by_block_and_street(self, block: str, street: str) -> Block | None:
        """
        Get block by block number and street.

        Args:
            block: Block number
            street: Street name

        Returns:
            Block if found, None otherwise
        """
        query = select(Block).where(and_(Block.block == block, Block.street == street))
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def get_by_town(self, town: str) -> list[Block]:
        """
        Get all blocks in a town.

        Args:
            town: Town name

        Returns:
            List of blocks
        """
        query = select(Block).where(Block.town == town)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def search_by_address(self, query_string: str) -> list[Block]:
        """
        Search blocks by address (block, street, or town).

        Args:
            query_string: Search query

        Returns:
            List of matching blocks
        """
        search_pattern = f"%{query_string}%"
        query = select(Block).where(
            Block.block.ilike(search_pattern)
            | Block.street.ilike(search_pattern)
            | Block.town.ilike(search_pattern)
        )
        result = self.session.execute(query)
        return list(result.scalars().all())


class POIRepository(BaseRepository[POI]):
    """Repository for POI model with custom queries."""

    def __init__(self, session: Session):
        """Initialize POIRepository."""
        super().__init__(session, POI)

    def get_by_type(self, poi_type: POIType) -> list[POI]:
        """
        Get all POIs of a specific type.

        Args:
            poi_type: POI type

        Returns:
            List of POIs
        """
        query = select(POI).where(POI.poi_type == poi_type)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_within_radius(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        poi_type: POIType | None = None,
    ) -> list[POI]:
        """
        Get POIs within a radius of a point.

        Uses Haversine formula approximation for distance calculation.

        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_km: Radius in kilometers
            poi_type: Optional POI type filter

        Returns:
            List of POIs within radius
        """
        # Haversine formula approximation
        lat_delta = radius_km / 111.32
        lon_delta = radius_km / (111.32 * func.cos(func.radians(latitude)))

        conditions: list[Any] = [
            POI.latitude.between(latitude - lat_delta, latitude + lat_delta),
            POI.longitude.between(longitude - lon_delta, longitude + lon_delta),
        ]

        if poi_type:
            conditions.append(POI.poi_type == poi_type)

        query = select(POI).where(and_(*conditions))
        result = self.session.execute(query)
        return list(result.scalars().all())


class LeadRepository(BaseRepository[Lead]):
    """Repository for Lead model with custom queries."""

    def __init__(self, session: Session):
        """Initialize LeadRepository."""
        super().__init__(session, Lead)

    def get_by_status(self, status: LeadStatus) -> list[Lead]:
        """
        Get leads by status.

        Args:
            status: Lead status

        Returns:
            List of leads
        """
        query = select(Lead).where(Lead.status == status).order_by(Lead.created_at.desc())
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_recent(self, limit: int = 10, status_filter: LeadStatus | None = None) -> list[Lead]:
        """
        Get recent leads with optional status filter.

        Args:
            limit: Maximum number of leads to return
            status_filter: Optional status filter

        Returns:
            List of recent leads
        """
        query = select(Lead)
        if status_filter:
            query = query.where(Lead.status == status_filter)
        query = query.order_by(Lead.created_at.desc()).limit(limit)
        result = self.session.execute(query)
        return list(result.scalars().all())


class IngestionRunRepository(BaseRepository[IngestionRun]):
    """Repository for IngestionRun model with custom queries."""

    def __init__(self, session: Session):
        """Initialize IngestionRunRepository."""
        super().__init__(session, IngestionRun)

    def get_latest_by_dataset(self, dataset_name: str) -> IngestionRun | None:
        """
        Get the latest ingestion run for a dataset.

        Args:
            dataset_name: Dataset name

        Returns:
            Latest ingestion run if found, None otherwise
        """
        query = (
            select(IngestionRun)
            .where(IngestionRun.dataset_name == dataset_name)
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )
        result = self.session.execute(query)
        return result.scalar_one_or_none()

    def get_failed_runs(self) -> list[IngestionRun]:
        """
        Get all failed ingestion runs.

        Returns:
            List of failed runs
        """
        query = (
            select(IngestionRun)
            .where(IngestionRun.status == "failed")
            .order_by(IngestionRun.started_at.desc())
        )
        result = self.session.execute(query)
        return list(result.scalars().all())


class BlockPOIRepository(BaseRepository):
    """Repository for BlockPOI model with proximity queries."""

    def __init__(self, session: Session):
        """Initialize BlockPOIRepository."""
        super().__init__(session, BlockPOI)

    def get_pois_near_block(
        self,
        block_id: int,
        max_distance_m: float = 1000,
        poi_type: POIType | None = None,
    ) -> list:
        """
        Get POIs within distance of block, ordered by proximity.

        Args:
            block_id: Block ID
            max_distance_m: Maximum distance in meters
            poi_type: Optional POI type filter

        Returns:
            List of BlockPOI records with POI details
        """

        query = (
            select(BlockPOI)
            .where(BlockPOI.block_id == block_id)
            .where(BlockPOI.distance_m <= max_distance_m)
            .order_by(BlockPOI.distance_m)
        )

        if poi_type:
            query = query.join(POI).where(POI.poi_type == poi_type)

        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_blocks_near_poi(self, poi_id: int, max_distance_m: float = 1000) -> list:
        """
        Get blocks within distance of POI, ordered by proximity.

        Args:
            poi_id: POI ID
            max_distance_m: Maximum distance in meters

        Returns:
            List of BlockPOI records
        """

        query = (
            select(BlockPOI)
            .where(BlockPOI.poi_id == poi_id)
            .where(BlockPOI.distance_m <= max_distance_m)
            .order_by(BlockPOI.distance_m)
        )

        result = self.session.execute(query)
        return list(result.scalars().all())

    def upsert_distances(self, block_id: int, poi_distances: list[dict[str, Any]]) -> int:
        """
        Bulk upsert distances for a block.

        Args:
            block_id: Block ID
            poi_distances: List of dicts with poi_id and distance_m

        Returns:
            Count of records inserted/updated
        """
        from sqlalchemy.dialects.postgresql import insert

        if not poi_distances:
            return 0

        # Prepare records
        records = [
            {
                "block_id": block_id,
                "poi_id": pd["poi_id"],
                "distance_m": pd["distance_m"],
            }
            for pd in poi_distances
        ]

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(BlockPOI).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["block_id", "poi_id"],
            set_={"distance_m": stmt.excluded.distance_m},
        )

        self.session.execute(stmt)
        self.session.commit()

        return len(records)
