"""Tests for repository pattern."""

from datetime import UTC, date, datetime

from resalelens.data.repositories import (
    BlockRepository,
    IngestionRunRepository,
    LeadRepository,
    POIRepository,
    TransactionRepository,
)
from resalelens.models import (
    POI,
    Block,
    IngestionRun,
    IngestionStatus,
    Lead,
    LeadStatus,
    POIType,
    Transaction,
)


class TestTransactionRepository:
    """Tests for TransactionRepository."""

    def test_get_by_block_and_date_range(self, db_session, sample_ingestion_run):
        """Test getting transactions by block and date range."""
        # Create test transactions
        txn1 = Transaction(
            date=date(2024, 1, 1),
            block="101",
            street="Test Street",
            flat_type="4 ROOM",
            storey_range="07 TO 09",
            floor_area_sqm=90.0,
            price=450000.0,
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=sample_ingestion_run.id,
        )
        txn2 = Transaction(
            date=date(2024, 2, 1),
            block="101",
            street="Test Street",
            flat_type="3 ROOM",
            storey_range="04 TO 06",
            floor_area_sqm=70.0,
            price=350000.0,
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add_all([txn1, txn2])
        db_session.commit()

        # Test repository
        repo = TransactionRepository(db_session)
        results = repo.get_by_block_and_date_range(
            "101", "Test Street", date(2024, 1, 1), date(2024, 1, 31)
        )

        assert len(results) == 1
        assert results[0].date == date(2024, 1, 1)

    def test_get_by_town_and_flat_type(self, db_session, sample_ingestion_run):
        """Test getting transactions by town and flat type."""
        txn = Transaction(
            date=date(2024, 1, 1),
            block="101",
            street="Test Street",
            flat_type="4 ROOM",
            storey_range="07 TO 09",
            floor_area_sqm=90.0,
            price=450000.0,
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add(txn)
        db_session.commit()

        repo = TransactionRepository(db_session)
        results = repo.get_by_town_and_flat_type(
            "Test Town", "4 ROOM", date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(results) == 1
        assert results[0].town == "Test Town"
        assert results[0].flat_type == "4 ROOM"


class TestBlockRepository:
    """Tests for BlockRepository."""

    def test_get_by_block_and_street(self, db_session):
        """Test getting block by block and street."""
        block = Block(
            block="101",
            street="Test Street",
            town="Test Town",
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)
        db_session.commit()

        repo = BlockRepository(db_session)
        result = repo.get_by_block_and_street("101", "Test Street")

        assert result is not None
        assert result.block == "101"
        assert result.street == "Test Street"

    def test_get_by_town(self, db_session):
        """Test getting blocks by town."""
        block1 = Block(
            block="101",
            street="Test Street 1",
            town="Test Town",
            last_updated=datetime.utcnow(),
        )
        block2 = Block(
            block="102",
            street="Test Street 2",
            town="Test Town",
            last_updated=datetime.utcnow(),
        )
        db_session.add_all([block1, block2])
        db_session.commit()

        repo = BlockRepository(db_session)
        results = repo.get_by_town("Test Town")

        assert len(results) == 2

    def test_search_by_address(self, db_session):
        """Test searching blocks by address."""
        block = Block(
            block="101",
            street="Ang Mo Kio Ave 3",
            town="Ang Mo Kio",
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)
        db_session.commit()

        repo = BlockRepository(db_session)
        results = repo.search_by_address("Ang Mo Kio")

        assert len(results) == 1
        assert results[0].town == "Ang Mo Kio"


class TestPOIRepository:
    """Tests for POIRepository."""

    def test_get_by_type(self, db_session):
        """Test getting POIs by type."""
        poi1 = POI(
            poi_type=POIType.MRT,
            name="Test MRT",
            latitude=1.3521,
            longitude=103.8198,
            last_updated=datetime.utcnow(),
        )
        poi2 = POI(
            poi_type=POIType.SCHOOL,
            name="Test School",
            latitude=1.3522,
            longitude=103.8199,
            last_updated=datetime.utcnow(),
        )
        db_session.add_all([poi1, poi2])
        db_session.commit()

        repo = POIRepository(db_session)
        results = repo.get_by_type(POIType.MRT)

        assert len(results) == 1
        assert results[0].poi_type == POIType.MRT


class TestLeadRepository:
    """Tests for LeadRepository."""

    def test_get_by_status(self, db_session):
        """Test getting leads by status."""
        lead1 = Lead(
            name="John", email="john@example.com", mobile="+65 9123 4567", status=LeadStatus.NEW
        )
        lead2 = Lead(
            name="Jane",
            email="jane@example.com",
            mobile="+65 8123 4567",
            status=LeadStatus.CONTACTED,
        )
        db_session.add_all([lead1, lead2])
        db_session.commit()

        repo = LeadRepository(db_session)
        results = repo.get_by_status(LeadStatus.NEW)

        assert len(results) == 1
        assert results[0].status == LeadStatus.NEW

    def test_get_recent(self, db_session):
        """Test getting recent leads."""
        lead1 = Lead(
            name="John", email="john@example.com", mobile="+65 9123 4567", status=LeadStatus.NEW
        )
        lead2 = Lead(
            name="Jane", email="jane@example.com", mobile="+65 8123 4567", status=LeadStatus.NEW
        )
        db_session.add_all([lead1, lead2])
        db_session.commit()

        repo = LeadRepository(db_session)
        results = repo.get_recent(limit=1)

        assert len(results) == 1


class TestIngestionRunRepository:
    """Tests for IngestionRunRepository."""

    def test_get_latest_by_dataset(self, db_session):
        """Test getting latest run by dataset."""

        run1 = IngestionRun(
            dataset_name="test",
            started_at=datetime(2024, 1, 1, tzinfo=UTC),
            status=IngestionStatus.SUCCESS,
            completed_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        run2 = IngestionRun(
            dataset_name="test",
            started_at=datetime(2024, 1, 2, tzinfo=UTC),
            status=IngestionStatus.SUCCESS,
            completed_at=datetime(2024, 1, 2, tzinfo=UTC),
        )
        db_session.add_all([run1, run2])
        db_session.commit()

        repo = IngestionRunRepository(db_session)
        result = repo.get_latest_by_dataset("test")

        assert result is not None
        assert result.started_at == datetime(2024, 1, 2, tzinfo=UTC)
