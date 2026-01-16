"""Block X-Ray service for property information features."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..models import POI, Block, BlockPOI, Transaction
from ..schemas.block_xray import (
    BlockFacilities,
    BlockXRayData,
    POIDistance,
    TrendDataPoint,
    UnitCompositionItem,
    VolatilityInfo,
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


def get_transaction_trends(
    block_id: int, session: Session
) -> list[TrendDataPoint]:
    """
    Get transaction trend data (quarterly median PSM over past 2 years).

    Args:
        block_id: Block ID to query
        session: Database session

    Returns:
        List of TrendDataPoint sorted by date (oldest to newest)
        Empty list if fewer than 5 transactions
    """
    # Get block info to filter transactions
    block = session.query(Block).filter(Block.id == block_id).first()
    if not block:
        return []

    # Query transactions for past 2 years
    two_years_ago = datetime.now(UTC) - timedelta(days=730)
    transactions = (
        session.query(Transaction)
        .filter(
            Transaction.block == block.block,
            Transaction.street == block.street,
            Transaction.date >= two_years_ago.date(),
        )
        .all()
    )

    # Return empty if insufficient data
    if len(transactions) < 5:
        return []

    # Group by quarter and calculate median PSM
    import statistics
    from collections import defaultdict

    quarterly_data: dict[str, list[float]] = defaultdict(list)

    for txn in transactions:
        # Calculate PSM (price per square meter)
        psm = txn.price / txn.floor_area_sqm if txn.floor_area_sqm > 0 else 0
        if psm == 0:
            continue

        # Determine quarter
        year = txn.date.year
        quarter = (txn.date.month - 1) // 3 + 1
        quarter_key = f"Q{quarter} {year}"

        quarterly_data[quarter_key].append(psm)

    # Calculate median for each quarter with data
    trends: list[TrendDataPoint] = []
    for quarter_key in sorted(
        quarterly_data.keys(),
        key=lambda q: (
            int(q.split()[1]),  # Year
            int(q.split()[0][1]),  # Quarter number
        ),
    ):
        psm_values = quarterly_data[quarter_key]
        if psm_values:
            median_psm = statistics.median(psm_values)
            trends.append(
                TrendDataPoint(quarter=quarter_key, median_psm=round(median_psm, 2))
            )

    return trends


def calculate_volatility(
    block_id: int, session: Session
) -> VolatilityInfo | None:
    """
    Calculate price volatility based on std dev of PSM over past 2 years.

    Volatility is classified using coefficient of variation (CV):
    - Low: CV < 10% (Stable Market)
    - Medium: 10% <= CV < 20% (Moderate Fluctuation)
    - High: CV >= 20% (High Volatility)

    Args:
        block_id: Block ID to query
        session: Database session

    Returns:
        VolatilityInfo or None if insufficient data (<5 transactions)
    """
    # Get block info
    block = session.query(Block).filter(Block.id == block_id).first()
    if not block:
        return None

    # Query transactions for past 2 years
    two_years_ago = datetime.now(UTC) - timedelta(days=730)
    transactions = (
        session.query(Transaction)
        .filter(
            Transaction.block == block.block,
            Transaction.street == block.street,
            Transaction.date >= two_years_ago.date(),
        )
        .all()
    )

    # Return None if insufficient data
    if len(transactions) < 5:
        return None

    # Calculate PSM for all transactions
    import statistics

    psm_values = [
        txn.price / txn.floor_area_sqm
        for txn in transactions
        if txn.floor_area_sqm > 0
    ]

    if len(psm_values) < 5:
        return None

    # Calculate std dev and mean
    std_dev = statistics.stdev(psm_values)
    mean_psm = statistics.mean(psm_values)

    # Calculate coefficient of variation (CV) as percentage
    cv = (std_dev / mean_psm * 100) if mean_psm > 0 else 0

    # Classify volatility
    if cv < 10:
        classification = "low"
        label = "Stable Market"
    elif cv < 20:
        classification = "medium"
        label = "Moderate Fluctuation"
    else:
        classification = "high"
        label = "High Volatility"

    return VolatilityInfo(
        std_dev=round(std_dev, 2),
        classification=classification,
        label=label,
    )


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

    # Get transaction analytics
    transaction_trends = get_transaction_trends(block_id, session)
    volatility = calculate_volatility(block_id, session)

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
        transaction_trends=transaction_trends,
        volatility=volatility,
        last_updated=block.last_updated,
    )
