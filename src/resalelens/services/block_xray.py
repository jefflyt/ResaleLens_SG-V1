"""Block X-Ray service for property information features."""

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import POI, Block, BlockPOI
from ..schemas.block_xray import (
    BlockFacilities,
    BlockXRayData,
    POIDistance,
    UnitCompositionItem,
)


def calculate_building_age(year_completed: int | None) -> int | None:
    """Calculate building age from year completed."""
    if year_completed is None:
        return None
    current_year = datetime.now().year
    return current_year - year_completed


def calculate_remaining_lease(lease_commence_year: int | None) -> int | None:
    """Calculate remaining lease years from lease commence year."""
    if lease_commence_year is None:
        return None
    current_year = datetime.now().year
    elapsed_years = current_year - lease_commence_year
    return max(0, 99 - elapsed_years)  # HDB leases are 99 years


def get_nearby_amenities(
    block_id: int, session: Session, max_distance_m: float = 500.0
) -> list[POIDistance]:
    """
    Get nearby POIs within specified distance.

    Args:
        block_id: Block ID to query
        session: Database session
        max_distance_m: Maximum distance in meters (default 500m)

    Returns:
        List of POI distances sorted by distance (nearest first)
    """
    results = (
        session.query(POI.name, POI.poi_type, BlockPOI.distance_m)
        .join(BlockPOI, POI.id == BlockPOI.poi_id)
        .filter(BlockPOI.block_id == block_id)
        .filter(BlockPOI.distance_m <= max_distance_m)
        .order_by(BlockPOI.distance_m)
        .limit(10)
        .all()
    )

    return [
        POIDistance(name=name, poi_type=poi_type.value, distance_m=float(distance))
        for name, poi_type, distance in results
    ]


def get_unit_composition(block: Block) -> list[UnitCompositionItem]:
    """
    Calculate unit composition from block data (sold + rental units).

    Args:
        block: Block model instance

    Returns:
        List of unit composition items with sold/rental breakdown and percentages
    """
    # Define room types with sold and rental counts
    room_types = [
        ("1-room", block.room_1_sold or 0, block.room_1_rental or 0),
        ("2-room", block.room_2_sold or 0, block.room_2_rental or 0),
        ("3-room", block.room_3_sold or 0, block.room_3_rental or 0),
        ("4-room", block.room_4_sold or 0, 0),  # No rental for 4-room
        ("5-room", block.room_5_sold or 0, 0),  # No rental for 5-room
        ("Executive", block.exec_sold or 0, 0),
        ("Multi-gen", block.multigen_sold or 0, 0),
        ("Studio", block.studio_apartment_sold or 0, 0),
    ]

    # Build composition list
    composition: list[dict[str, int | str]] = []
    total_units = 0

    for room_type, sold, rental in room_types:
        total = sold + rental
        if total > 0:  # Only include room types with units
            composition.append(
                {
                    "room_type": room_type,
                    "sold_units": sold,
                    "rental_units": rental,
                    "total_units": total,
                }
            )
            total_units += total

    if total_units == 0:
        return []

    # Calculate percentages and create final objects
    unit_composition: list[UnitCompositionItem] = []
    for item in composition:
        unit_composition.append(
            UnitCompositionItem(
                room_type=str(item["room_type"]),
                sold_units=int(item["sold_units"]),
                rental_units=int(item["rental_units"]),
                total_units=int(item["total_units"]),
                percentage=round((int(item["total_units"]) / total_units) * 100, 1),
            )
        )

    # Sort by total units descending
    unit_composition.sort(key=lambda x: x.total_units, reverse=True)

    return unit_composition


def get_block_xray(block_id: int, session: Session) -> BlockXRayData | None:
    """
    Get comprehensive Block X-Ray data including property information.

    Args:
        block_id: Block ID to query
        session: Database session

    Returns:
        BlockXRayData or None if block not found
    """
    block = session.query(Block).filter(Block.id == block_id).first()

    if not block:
        return None

    # Calculate derived fields
    building_age = calculate_building_age(block.year_completed)
    remaining_lease = calculate_remaining_lease(block.lease_commence_year)

    # Get nearby amenities
    nearby_amenities = get_nearby_amenities(block_id, session)

    # Get unit composition
    unit_composition = get_unit_composition(block)

    # Build facilities object
    facilities = BlockFacilities(
        commercial=block.commercial or False,
        market_hawker=block.market_hawker or False,
        multistorey_carpark=block.multistorey_carpark or False,
        precinct_pavilion=block.precinct_pavilion or False,
    )

    return BlockXRayData(
        block_id=block.id,
        block=block.block,
        street=block.street,
        town=block.town,
        postal_code=block.postal_code,
        lease_commence_year=block.lease_commence_year,
        remaining_lease_years=remaining_lease,
        building_age=building_age,
        max_floor_lvl=block.max_floor_lvl,
        year_completed=block.year_completed,
        total_dwelling_units=block.total_dwelling_units,
        facilities=facilities,
        nearby_amenities=nearby_amenities,
        unit_composition=unit_composition,
        last_updated=block.last_updated,
    )
