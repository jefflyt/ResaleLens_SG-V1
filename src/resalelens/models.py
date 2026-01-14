"""Database models for ResaleLens application."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# Enums
class POIType(str, PyEnum):
    """Point of Interest types."""

    MRT = "MRT"
    LRT = "LRT"
    SUPERMARKET = "supermarket"
    CLINIC = "clinic"
    PARK = "park"
    MALL = "mall"
    HAWKER = "hawker"
    SCHOOL = "school"


class LeadStatus(str, PyEnum):
    """Lead status enum."""

    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"


class IngestionStatus(str, PyEnum):
    """Ingestion run status enum."""

    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


# Models
class User(Base):
    """User model for admin authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class IngestionRun(Base):
    """Ingestion run tracking for data import auditing."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus), default=IngestionStatus.IN_PROGRESS, nullable=False
    )
    rows_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="ingestion_run", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_ingestion_runs_dataset_started", "dataset_name", "started_at"),
        Index("ix_ingestion_runs_status", "status"),
        CheckConstraint("rows_processed >= 0", name="check_rows_processed_nonnegative"),
    )

    def __repr__(self) -> str:
        return f"<IngestionRun(id={self.id}, dataset={self.dataset_name}, status={self.status})>"


class Transaction(Base):
    """HDB resale transaction records."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    block: Mapped[str] = mapped_column(String(50), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    flat_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storey_range: Mapped[str] = mapped_column(String(50), nullable=False)
    floor_area_sqm: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    lease_commence_date: Mapped[int] = mapped_column(Integer, nullable=False)
    town: Mapped[str] = mapped_column(String(100), nullable=False)
    flat_model: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    block_id: Mapped[int | None] = mapped_column(ForeignKey("blocks.id"), nullable=True)
    ingestion_run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    block_ref: Mapped[Block] = relationship("Block", back_populates="transactions")
    ingestion_run: Mapped[IngestionRun] = relationship(
        "IngestionRun", back_populates="transactions"
    )

    # Computed property
    @property
    def psm(self) -> float:
        """Price per square meter."""
        return float(self.price) / float(self.floor_area_sqm)

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint(
            "block",
            "street",
            "flat_type",
            "date",
            "storey_range",
            "floor_area_sqm",
            name="uq_transaction_details",
        ),
        Index(
            "ix_transactions_block_street_flat_type_date", "block", "street", "flat_type", "date"
        ),
        Index("ix_transactions_town_flat_type_date", "town", "flat_type", "date"),
        Index("ix_transactions_lat_lng", "latitude", "longitude"),
        Index("ix_transactions_block_id", "block_id"),
        CheckConstraint("floor_area_sqm > 0", name="check_floor_area_positive"),
        CheckConstraint("price > 0", name="check_price_positive"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_longitude_range"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, block={self.block}, street={self.street}, date={self.date})>"


class Block(Base):
    """HDB block metadata."""

    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block: Mapped[str] = mapped_column(String(50), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    town: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    lease_commence_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flat_mix_distribution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # HDB Property Information fields
    # Building characteristics
    max_floor_lvl: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_dwelling_units: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Facility flags
    residential: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=True)
    commercial: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    market_hawker: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    multistorey_carpark: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    precinct_pavilion: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    miscellaneous: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)

    # Unit mix - sold units
    room_1_sold: Mapped[int | None] = mapped_column("1room_sold", Integer, nullable=True)
    room_2_sold: Mapped[int | None] = mapped_column("2room_sold", Integer, nullable=True)
    room_3_sold: Mapped[int | None] = mapped_column("3room_sold", Integer, nullable=True)
    room_4_sold: Mapped[int | None] = mapped_column("4room_sold", Integer, nullable=True)
    room_5_sold: Mapped[int | None] = mapped_column("5room_sold", Integer, nullable=True)
    exec_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    multigen_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    studio_apartment_sold: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Unit mix - rental units
    room_1_rental: Mapped[int | None] = mapped_column("1room_rental", Integer, nullable=True)
    room_2_rental: Mapped[int | None] = mapped_column("2room_rental", Integer, nullable=True)
    room_3_rental: Mapped[int | None] = mapped_column("3room_rental", Integer, nullable=True)
    other_room_rental: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="block_ref"
    )
    nearby_pois: Mapped[list[BlockPOI]] = relationship("BlockPOI", back_populates="block")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("block", "street", name="uq_block_street"),
        Index("ix_blocks_block_street", "block", "street"),
        Index("ix_blocks_town", "town"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_block_latitude_range"),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180", name="check_block_longitude_range"
        ),
        CheckConstraint("lease_commence_year >= 1960", name="check_lease_commence_year_valid"),
    )

    def __repr__(self) -> str:
        return f"<Block(id={self.id}, block={self.block}, street={self.street}, town={self.town})>"


class POI(Base):
    """Points of Interest (MRT, amenities, etc.)."""

    __tablename__ = "pois"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poi_type: Mapped[POIType] = mapped_column(Enum(POIType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    nearby_blocks: Mapped[list[BlockPOI]] = relationship("BlockPOI", back_populates="poi")

    # Indexes
    __table_args__ = (
        Index("ix_pois_type_lat_lng", "poi_type", "latitude", "longitude"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_poi_latitude_range"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_poi_longitude_range"),
    )

    def __repr__(self) -> str:
        return f"<POI(id={self.id}, type={self.poi_type}, name={self.name})>"


class Lead(Base):
    """Lead/callback requests from users."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_window: Mapped[str | None] = mapped_column(String(100), nullable=True)
    budget_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_towns: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    flat_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    timeline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_timer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    financing_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    filter_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    shortlist_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_leads_created_status", "created_at", "status"),
        Index("ix_leads_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name={self.name}, email={self.email}, status={self.status})>"


class BlockPOI(Base):
    """Junction table for Block-POI relationships with pre-calculated distances."""

    __tablename__ = "block_pois"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id"), nullable=False)
    poi_id: Mapped[int] = mapped_column(ForeignKey("pois.id"), nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    block: Mapped[Block] = relationship("Block", back_populates="nearby_pois")
    poi: Mapped[POI] = relationship("POI", back_populates="nearby_blocks")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("block_id", "poi_id", name="uq_block_poi"),
        Index("ix_block_pois_block_id_distance", "block_id", "distance_m"),
        Index("ix_block_pois_poi_id", "poi_id"),
        CheckConstraint("distance_m >= 0", name="check_distance_positive"),
    )

    def __repr__(self) -> str:
        return f"<BlockPOI(block_id={self.block_id}, poi_id={self.poi_id}, distance={self.distance_m}m)>"
