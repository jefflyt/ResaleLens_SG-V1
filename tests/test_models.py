"""Tests for database models."""

from datetime import date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from resalelens.models import (
    POI,
    Block,
    BlockPOI,
    IngestionRun,
    IngestionStatus,
    Lead,
    LeadStatus,
    POIType,
    Transaction,
    User,
)


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.created_at is not None

    def test_user_unique_email(self, db_session):
        """Test that user email must be unique."""
        user1 = User(email="test@example.com", hashed_password="hash1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="test@example.com", hashed_password="hash2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestIngestionRunModel:
    """Tests for IngestionRun model."""

    def test_ingestion_run_creation(self, db_session):
        """Test creating an ingestion run."""
        run = IngestionRun(
            dataset_name="test_dataset",
            started_at=datetime.utcnow(),
            status=IngestionStatus.IN_PROGRESS,
        )
        db_session.add(run)
        db_session.commit()

        assert run.id is not None
        assert run.dataset_name == "test_dataset"
        assert run.status == IngestionStatus.IN_PROGRESS
        assert run.rows_processed == 0

    def test_ingestion_run_completed(self, db_session):
        """Test completing an ingestion run."""
        run = IngestionRun(
            dataset_name="test_dataset",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
            completed_at=datetime.utcnow(),
            rows_processed=100,
        )
        db_session.add(run)
        db_session.commit()

        assert run.status == IngestionStatus.SUCCESS
        assert run.rows_processed == 100
        assert run.completed_at is not None


class TestTransactionModel:
    """Tests for Transaction model."""

    def test_transaction_creation(self, db_session, sample_ingestion_run):
        """Test creating a transaction."""
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
            latitude=1.3521,
            longitude=103.8198,
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add(txn)
        db_session.commit()

        assert txn.id is not None
        assert txn.block == "101"
        assert txn.price == 450000.0

    def test_transaction_psm_property(self, db_session, sample_ingestion_run):
        """Test PSM computed property."""
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

        assert txn.psm == 5000.0  # 450000 / 90

    def test_transaction_unique_constraint(self, db_session, sample_ingestion_run):
        """Test unique constraint on transaction details."""
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
        db_session.add(txn1)
        db_session.commit()

        txn2 = Transaction(
            date=date(2024, 1, 1),
            block="101",
            street="Test Street",
            flat_type="4 ROOM",
            storey_range="07 TO 09",
            floor_area_sqm=90.0,
            price=460000.0,  # Different price but same other details
            lease_commence_date=1990,
            town="Test Town",
            flat_model="Improved",
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add(txn2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestBlockModel:
    """Tests for Block model."""

    def test_block_creation(self, db_session):
        """Test creating a block."""
        block = Block(
            block="101",
            street="Test Street",
            town="Test Town",
            postal_code="520101",
            latitude=1.3521,
            longitude=103.8198,
            lease_commence_year=1990,
            flat_mix_distribution={"3 ROOM": 40, "4 ROOM": 60},
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)
        db_session.commit()

        assert block.id is not None
        assert block.block == "101"
        assert block.flat_mix_distribution == {"3 ROOM": 40, "4 ROOM": 60}

    def test_block_unique_constraint(self, db_session):
        """Test unique constraint on block and street."""
        block1 = Block(
            block="101",
            street="Test Street",
            town="Test Town",
            last_updated=datetime.utcnow(),
        )
        db_session.add(block1)
        db_session.commit()

        block2 = Block(
            block="101",
            street="Test Street",
            town="Another Town",  # Different town but same block/street
            last_updated=datetime.utcnow(),
        )
        db_session.add(block2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestPOIModel:
    """Tests for POI model."""

    def test_poi_creation(self, db_session):
        """Test creating a POI."""
        poi = POI(
            poi_type=POIType.MRT,
            name="Test MRT",
            latitude=1.3521,
            longitude=103.8198,
            last_updated=datetime.utcnow(),
        )
        db_session.add(poi)
        db_session.commit()

        assert poi.id is not None
        assert poi.poi_type == POIType.MRT
        assert poi.name == "Test MRT"


class TestLeadModel:
    """Tests for Lead model."""

    def test_lead_creation(self, db_session):
        """Test creating a lead."""
        lead = Lead(
            name="John Doe",
            email="john@example.com",
            mobile="+65 9123 4567",
            budget_range="400k-500k",
            preferred_towns=["Ang Mo Kio", "Bedok"],
            flat_types=["3 ROOM", "4 ROOM"],
            first_timer=True,
            status=LeadStatus.NEW,
        )
        db_session.add(lead)
        db_session.commit()

        assert lead.id is not None
        assert lead.name == "John Doe"
        assert lead.status == LeadStatus.NEW
        assert lead.preferred_towns == ["Ang Mo Kio", "Bedok"]
        assert lead.flat_types == ["3 ROOM", "4 ROOM"]

    def test_lead_json_fields(self, db_session):
        """Test JSON field serialization."""
        lead = Lead(
            name="Jane Doe",
            email="jane@example.com",
            mobile="+65 8123 4567",
            filter_snapshot={"town": "Bedok", "flat_type": "4 ROOM"},
            shortlist_snapshot={"blocks": ["101", "202"]},
        )
        db_session.add(lead)
        db_session.commit()

        db_session.refresh(lead)
        assert lead.filter_snapshot == {"town": "Bedok", "flat_type": "4 ROOM"}
        assert lead.shortlist_snapshot == {"blocks": ["101", "202"]}


class TestTransactionBlockRelationship:
    """Tests for Transaction-Block foreign key relationship (PR1.3a)."""

    def test_transaction_block_ref_relationship(self, db_session):
        """Test Transaction.block_ref loads Block correctly."""
        # Create a block
        block = Block(
            block="101",
            street="TEST STREET",
            town="TEST TOWN",
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)
        db_session.commit()

        # Create ingestion run
        run = IngestionRun(
            dataset_name="test",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        db_session.commit()

        # Create transaction with block_id
        txn = Transaction(
            date=date(2024, 1, 1),
            block="101",
            street="TEST STREET",
            flat_type="4 ROOM",
            storey_range="07 TO 09",
            floor_area_sqm=90.0,
            price=450000.0,
            lease_commence_date=1990,
            town="TEST TOWN",
            flat_model="Improved",
            block_id=block.id,
            ingestion_run_id=run.id,
        )
        db_session.add(txn)
        db_session.commit()

        # Test relationship
        db_session.refresh(txn)
        assert txn.block_ref is not None
        assert txn.block_ref.id == block.id
        assert txn.block_ref.block == "101"
        assert txn.block_ref.street == "TEST STREET"

    def test_block_transactions_relationship(self, db_session):
        """Test Block.transactions returns list of transactions."""
        # Create a block
        block = Block(
            block="202",
            street="ANOTHER STREET",
            town="ANOTHER TOWN",
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)
        db_session.commit()

        # Create ingestion run
        run = IngestionRun(
            dataset_name="test",
            started_at=datetime.utcnow(),
            status=IngestionStatus.SUCCESS,
        )
        db_session.add(run)
        db_session.commit()

        # Create multiple transactions for same block
        for i in range(3):
            txn = Transaction(
                date=date(2024, 1, i + 1),
                block="202",
                street="ANOTHER STREET",
                flat_type="4 ROOM",
                storey_range=f"{i:02d} TO {i+2:02d}",
                floor_area_sqm=90.0 + i,
                price=450000.0 + (i * 10000),
                lease_commence_date=1990,
                town="ANOTHER TOWN",
                flat_model="Improved",
                block_id=block.id,
                ingestion_run_id=run.id,
            )
            db_session.add(txn)
        db_session.commit()

        # Test relationship
        db_session.refresh(block)
        assert len(block.transactions) == 3
        assert all(t.block_id == block.id for t in block.transactions)

    def test_foreign_key_constraint(self, db_session, sample_ingestion_run):
        """Test foreign key prevents orphaned transactions."""
        # Try to create transaction with invalid block_id
        txn = Transaction(
            date=date(2024, 1, 1),
            block="999",
            street="NONEXISTENT STREET",
            flat_type="4 ROOM",
            storey_range="07 TO 09",
            floor_area_sqm=90.0,
            price=450000.0,
            lease_commence_date=1990,
            town="NONEXISTENT TOWN",
            flat_model="Improved",
            block_id=99999,  # Invalid block_id
            ingestion_run_id=sample_ingestion_run.id,
        )
        db_session.add(txn)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestBlockPOIModel:
    """Tests for BlockPOI model (PR1.3b)."""

    def test_block_poi_creation(self, db_session):
        """Test creating a BlockPOI record."""
        # Create block
        block = Block(
            block="101",
            street="TEST STREET",
            town="TEST TOWN",
            latitude=1.3521,
            longitude=103.8198,
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)

        # Create POI
        poi = POI(
            poi_type=POIType.MRT,
            name="Test MRT",
            latitude=1.3700,
            longitude=103.8494,
            last_updated=datetime.utcnow(),
        )
        db_session.add(poi)
        db_session.commit()

        # Create BlockPOI
        block_poi = BlockPOI(
            block_id=block.id,
            poi_id=poi.id,
            distance_m=2127.0,  # Calculated distance
        )
        db_session.add(block_poi)
        db_session.commit()

        assert block_poi.id is not None
        assert block_poi.block_id == block.id
        assert block_poi.poi_id == poi.id
        assert block_poi.distance_m == 2127.0

    def test_block_poi_unique_constraint(self, db_session):
        """Test unique constraint on (block_id, poi_id)."""
        # Create block and POI
        block = Block(
            block="101",
            street="TEST STREET",
            town="TEST TOWN",
            last_updated=datetime.utcnow(),
        )
        poi = POI(
            poi_type=POIType.MRT,
            name="Test MRT",
            latitude=1.3700,
            longitude=103.8494,
            last_updated=datetime.utcnow(),
        )
        db_session.add_all([block, poi])
        db_session.commit()

        # Create first BlockPOI
        bp1 = BlockPOI(block_id=block.id, poi_id=poi.id, distance_m=1000.0)
        db_session.add(bp1)
        db_session.commit()

        # Try to create duplicate
        bp2 = BlockPOI(block_id=block.id, poi_id=poi.id, distance_m=2000.0)
        db_session.add(bp2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_block_nearby_pois_relationship(self, db_session):
        """Test Block.nearby_pois relationship."""
        # Create block
        block = Block(
            block="101",
            street="TEST STREET",
            town="TEST TOWN",
            latitude=1.3521,
            longitude=103.8198,
            last_updated=datetime.utcnow(),
        )
        db_session.add(block)

        # Create multiple POIs
        pois = []
        for i in range(3):
            poi = POI(
                poi_type=POIType.MRT,
                name=f"Test MRT {i}",
                latitude=1.3700 + (i * 0.01),
                longitude=103.8494,
                last_updated=datetime.utcnow(),
            )
            pois.append(poi)
            db_session.add(poi)
        db_session.commit()

        # Create BlockPOI records
        for i, poi in enumerate(pois):
            bp = BlockPOI(
                block_id=block.id,
                poi_id=poi.id,
                distance_m=1000.0 + (i * 500),
            )
            db_session.add(bp)
        db_session.commit()

        # Test relationship
        db_session.refresh(block)
        assert len(block.nearby_pois) == 3
        assert all(bp.block_id == block.id for bp in block.nearby_pois)
