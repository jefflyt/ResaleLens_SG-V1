"""Tests for database models."""

from datetime import date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from resalelens.models import (
    POI,
    Block,
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
