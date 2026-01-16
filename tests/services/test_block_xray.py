"""Tests for Block X-Ray service."""

from datetime import datetime

from sqlalchemy.orm import Session

from resalelens.models import POI, Block, BlockPOI, POIType
from resalelens.services.block_xray import (
    calculate_building_age,
    calculate_remaining_lease,
    get_block_xray,
    get_nearby_amenities,
    get_unit_composition,
)


def test_calculate_building_age():
    """Test building age calculation."""
    current_year = datetime.now().year

    # Normal case
    age = calculate_building_age(2000)
    assert age == current_year - 2000

    # None case
    assert calculate_building_age(None) is None


def test_calculate_remaining_lease():
    """Test remaining lease calculation."""
    current_year = datetime.now().year

    # Block with 50 years elapsed
    lease_year = current_year - 50
    remaining = calculate_remaining_lease(lease_year)
    assert remaining == 49  # 99 - 50

    # Very old block (>99 years)
    old_lease_year = current_year - 100
    remaining = calculate_remaining_lease(old_lease_year)
    assert remaining == 0  # Cannot be negative

    # None case
    assert calculate_remaining_lease(None) is None


def test_get_unit_composition_with_data():
    """Test unit composition calculation with sold and rental data."""
    block = Block(
        id=1,
        block="123",
        street="Test St",
        town="Test Town",
        room_3_sold=138,
        room_5_sold=2,
        room_4_sold=1,
        room_2_sold=1,
        room_1_rental=5,
        room_2_rental=3,
    )

    unit_composition = get_unit_composition(block)

    # Should have 5 room types (3-room, 5-room, 4-room, 2-room, 1-room rental)
    assert len(unit_composition) == 5

    # Should be sorted by total units descending
    assert unit_composition[0].room_type == "3-room"
    assert unit_composition[0].sold_units == 138
    assert unit_composition[0].rental_units == 0
    assert unit_composition[0].total_units == 138
    assert unit_composition[0].percentage == 92.0  # 138/150 * 100

    # Check 2-room has both sold and rental
    room_2 = next(item for item in unit_composition if item.room_type == "2-room")
    assert room_2.sold_units == 1
    assert room_2.rental_units == 3
    assert room_2.total_units == 4


def test_get_unit_composition_empty():
    """Test unit composition with no data."""
    block = Block(
        id=1,
        block="123",
        street="Test St",
        town="Test Town",
    )

    unit_composition = get_unit_composition(block)
    assert unit_composition == []


def test_get_nearby_amenities(db_session: Session):
    """Test nearby amenities query."""
    # Create test data
    block = Block(
        block="123",
        street="Test St",
        town="Test Town",
        latitude=1.3521,
        longitude=103.8198,
    )
    db_session.add(block)
    db_session.flush()

    # Add POIs
    mrt = POI(
        poi_type=POIType.MRT,
        name="Test MRT",
        latitude=1.3522,
        longitude=103.8199,
    )
    supermarket = POI(
        poi_type=POIType.SUPERMARKET,
        name="Test Supermarket",
        latitude=1.3523,
        longitude=103.8200,
    )
    far_poi = POI(
        poi_type=POIType.CLINIC,
        name="Far Clinic",
        latitude=1.4000,
        longitude=103.9000,
    )

    db_session.add_all([mrt, supermarket, far_poi])
    db_session.flush()

    # Add BlockPOI relationships
    block_poi_1 = BlockPOI(block_id=block.id, poi_id=mrt.id, distance_m=350.0)
    block_poi_2 = BlockPOI(block_id=block.id, poi_id=supermarket.id, distance_m=280.0)
    block_poi_3 = BlockPOI(block_id=block.id, poi_id=far_poi.id, distance_m=1200.0)

    db_session.add_all([block_poi_1, block_poi_2, block_poi_3])
    db_session.commit()

    # Query nearby amenities (within 500m)
    amenities = get_nearby_amenities(block.id, db_session, max_distance_m=500.0)

    # Should only return 2 POIs within 500m, sorted by distance
    assert len(amenities) == 2
    assert amenities[0].name == "Test Supermarket"
    assert amenities[0].distance_m == 280.0
    assert amenities[1].name == "Test MRT"
    assert amenities[1].distance_m == 350.0


def test_get_block_xray_success(db_session: Session):
    """Test successful Block X-Ray data retrieval."""
    # Create test block with full data
    block = Block(
        block="123",
        street="Test St",
        town="Test Town",
        postal_code="123456",
        latitude=1.3521,
        longitude=103.8198,
        lease_commence_year=1990,
        year_completed=1992,
        max_floor_lvl=12,
        total_dwelling_units=142,
        commercial=True,
        market_hawker=False,
        multistorey_carpark=False,
        precinct_pavilion=False,
        room_3_sold=138,
        room_5_sold=2,
        room_4_sold=1,
        room_2_sold=1,
    )
    db_session.add(block)
    db_session.commit()

    # Get Block X-Ray data
    data = get_block_xray(block.id, db_session)

    assert data is not None
    assert data.block_id == block.id
    assert data.block == "123"
    assert data.street == "Test St"
    assert data.postal_code == "123456"
    assert data.year_completed == 1992
    assert data.building_age is not None
    assert data.max_floor_lvl == 12
    assert data.total_dwelling_units == 142
    assert data.facilities.commercial is True
    assert data.facilities.market_hawker is False
    assert len(data.unit_composition) == 4


def test_get_block_xray_not_found(db_session: Session):
    """Test Block X-Ray with non-existent block."""
    data = get_block_xray(99999, db_session)
    assert data is None


def test_get_block_xray_minimal_data(db_session: Session):
    """Test Block X-Ray with minimal block data."""
    block = Block(
        block="456",
        street="Minimal St",
        town="Test Town",
    )
    db_session.add(block)
    db_session.commit()

    data = get_block_xray(block.id, db_session)

    assert data is not None
    assert data.block_id == block.id
    assert data.year_completed is None
    assert data.building_age is None
    assert data.remaining_lease_years is None
    assert data.unit_composition == []
    assert data.nearby_amenities == []
