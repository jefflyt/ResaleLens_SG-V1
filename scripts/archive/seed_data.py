"""Seed development database with realistic test data."""

import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from resalelens.database import SessionLocal, engine
from resalelens.models import (
    POI,
    Base,
    Block,
    IngestionRun,
    IngestionStatus,
    Lead,
    LeadStatus,
    POIType,
    Transaction,
)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Created all database tables")


def seed_ingestion_runs(session: Session) -> list[IngestionRun]:
    """Create ingestion run records."""
    ingestion_runs = [
        IngestionRun(
            dataset_name="hdb_transactions",
            started_at=datetime.utcnow() - timedelta(days=30),
            completed_at=datetime.utcnow() - timedelta(days=30, hours=-1),
            status=IngestionStatus.SUCCESS,
            rows_processed=100,
            error_summary=None,
        ),
        IngestionRun(
            dataset_name="hdb_blocks",
            started_at=datetime.utcnow() - timedelta(days=29),
            completed_at=datetime.utcnow() - timedelta(days=29, hours=-1),
            status=IngestionStatus.SUCCESS,
            rows_processed=15,
            error_summary=None,
        ),
        IngestionRun(
            dataset_name="pois",
            started_at=datetime.utcnow() - timedelta(days=28),
            completed_at=datetime.utcnow() - timedelta(days=28, hours=-1),
            status=IngestionStatus.SUCCESS,
            rows_processed=30,
            error_summary=None,
        ),
    ]
    session.add_all(ingestion_runs)
    session.commit()
    for run in ingestion_runs:
        session.refresh(run)
    print(f"✅ Created {len(ingestion_runs)} ingestion runs")
    return ingestion_runs


def seed_blocks(session: Session) -> list[Block]:
    """Create block records."""
    blocks_data = [
        # Ang Mo Kio
        {
            "block": "101",
            "street": "Ang Mo Kio Ave 3",
            "town": "Ang Mo Kio",
            "postal_code": "560101",
            "lat": 1.3691,
            "lng": 103.8454,
            "lease_year": 1980,
            "flat_mix": {"3 ROOM": 40, "4 ROOM": 60, "5 ROOM": 20},
        },
        {
            "block": "212",
            "street": "Ang Mo Kio Ave 3",
            "town": "Ang Mo Kio",
            "postal_code": "560212",
            "lat": 1.3701,
            "lng": 103.8464,
            "lease_year": 1985,
            "flat_mix": {"3 ROOM": 30, "4 ROOM": 70},
        },
        {
            "block": "320",
            "street": "Ang Mo Kio Ave 1",
            "town": "Ang Mo Kio",
            "postal_code": "560320",
            "lat": 1.3680,
            "lng": 103.8470,
            "lease_year": 1990,
            "flat_mix": {"4 ROOM": 50, "5 ROOM": 50},
        },
        # Bedok
        {
            "block": "85",
            "street": "Bedok North St 4",
            "town": "Bedok",
            "postal_code": "460085",
            "lat": 1.3307,
            "lng": 103.9280,
            "lease_year": 1982,
            "flat_mix": {"2 ROOM": 20, "3 ROOM": 50, "4 ROOM": 30},
        },
        {
            "block": "123",
            "street": "Bedok North Ave 3",
            "town": "Bedok",
            "postal_code": "460123",
            "lat": 1.3320,
            "lng": 103.9300,
            "lease_year": 1987,
            "flat_mix": {"3 ROOM": 45, "4 ROOM": 55},
        },
        {
            "block": "201",
            "street": "Bedok North Road",
            "town": "Bedok",
            "postal_code": "460201",
            "lat": 1.3290,
            "lng": 103.9250,
            "lease_year": 1995,
            "flat_mix": {"4 ROOM": 80, "5 ROOM": 20},
        },
        # Clementi
        {
            "block": "301",
            "street": "Clementi Ave 2",
            "town": "Clementi",
            "postal_code": "120301",
            "lat": 1.3150,
            "lng": 103.7650,
            "lease_year": 1983,
            "flat_mix": {"3 ROOM": 35, "4 ROOM": 65},
        },
        {
            "block": "442",
            "street": "Clementi Ave 3",
            "town": "Clementi",
            "postal_code": "120442",
            "lat": 1.3165,
            "lng": 103.7668,
            "lease_year": 1988,
            "flat_mix": {"4 ROOM": 60, "5 ROOM": 40},
        },
        {
            "block": "523",
            "street": "Clementi Ave 5",
            "town": "Clementi",
            "postal_code": "120523",
            "lat": 1.3140,
            "lng": 103.7640,
            "lease_year": 2000,
            "flat_mix": {"3 ROOM": 25, "4 ROOM": 50, "5 ROOM": 25},
        },
        # Hougang
        {
            "block": "105",
            "street": "Hougang Ave 1",
            "town": "Hougang",
            "postal_code": "530105",
            "lat": 1.3710,
            "lng": 103.8910,
            "lease_year": 1984,
            "flat_mix": {"3 ROOM": 40, "4 ROOM": 60},
        },
        {
            "block": "221",
            "street": "Hougang St 21",
            "town": "Hougang",
            "postal_code": "530221",
            "lat": 1.3700,
            "lng": 103.8890,
            "lease_year": 1992,
            "flat_mix": {"4 ROOM": 70, "5 ROOM": 30},
        },
        {
            "block": "342",
            "street": "Hougang Ave 5",
            "town": "Hougang",
            "postal_code": "530342",
            "lat": 1.3725,
            "lng": 103.8935,
            "lease_year": 1997,
            "flat_mix": {"3 ROOM": 20, "4 ROOM": 50, "5 ROOM": 30},
        },
        # Tampines
        {
            "block": "101",
            "street": "Tampines St 11",
            "town": "Tampines",
            "postal_code": "521101",
            "lat": 1.3456,
            "lng": 103.9456,
            "lease_year": 1986,
            "flat_mix": {"3 ROOM": 45, "4 ROOM": 55},
        },
        {
            "block": "234",
            "street": "Tampines St 21",
            "town": "Tampines",
            "postal_code": "521234",
            "lat": 1.3498,
            "lng": 103.9500,
            "lease_year": 1993,
            "flat_mix": {"4 ROOM": 65, "5 ROOM": 35},
        },
        {
            "block": "456",
            "street": "Tampines Ave 4",
            "town": "Tampines",
            "postal_code": "520456",
            "lat": 1.3445,
            "lng": 103.9440,
            "lease_year": 2005,
            "flat_mix": {"3 ROOM": 30, "4 ROOM": 40, "5 ROOM": 30},
        },
    ]

    blocks = []
    for data in blocks_data:
        block = Block(
            block=data["block"],
            street=data["street"],
            town=data["town"],
            postal_code=data["postal_code"],
            latitude=data["lat"],
            longitude=data["lng"],
            lease_commence_year=data["lease_year"],
            flat_mix_distribution=data["flat_mix"],
            last_updated=datetime.utcnow(),
        )
        blocks.append(block)

    session.add_all(blocks)
    session.commit()
    for block in blocks:
        session.refresh(block)
    print(f"✅ Created {len(blocks)} blocks")
    return blocks


def seed_pois(session: Session) -> list[POI]:
    """Create POI records."""
    pois_data = [
        # MRT stations
        {"type": POIType.MRT, "name": "Ang Mo Kio MRT", "lat": 1.3700, "lng": 103.8495},
        {"type": POIType.MRT, "name": "Bedok MRT", "lat": 1.3240, "lng": 103.9300},
        {"type": POIType.MRT, "name": "Clementi MRT", "lat": 1.3150, "lng": 103.7655},
        {"type": POIType.MRT, "name": "Hougang MRT", "lat": 1.3710, "lng": 103.8930},
        {"type": POIType.MRT, "name": "Tampines MRT", "lat": 1.3530, "lng": 103.9450},
        # Schools
        {
            "type": POIType.SCHOOL,
            "name": "CHIJ St. Nicholas Girls' School",
            "lat": 1.3710,
            "lng": 103.8440,
        },
        {
            "type": POIType.SCHOOL,
            "name": "Bedok View Secondary School",
            "lat": 1.3320,
            "lng": 103.9350,
        },
        {"type": POIType.SCHOOL, "name": "Clementi Primary School", "lat": 1.3140, "lng": 103.7700},
        {"type": POIType.SCHOOL, "name": "Hougang Primary School", "lat": 1.3680, "lng": 103.8900},
        {"type": POIType.SCHOOL, "name": "Tampines Primary School", "lat": 1.3450, "lng": 103.9420},
        # Supermarkets
        {
            "type": POIType.SUPERMARKET,
            "name": "NTUC FairPrice AMK Hub",
            "lat": 1.3690,
            "lng": 103.8480,
        },
        {"type": POIType.SUPERMARKET, "name": "Giant Bedok North", "lat": 1.3300, "lng": 103.9270},
        {
            "type": POIType.SUPERMARKET,
            "name": "Cold Storage Clementi Mall",
            "lat": 1.3155,
            "lng": 103.7645,
        },
        {
            "type": POIType.SUPERMARKET,
            "name": "NTUC FairPrice Hougang Mall",
            "lat": 1.3715,
            "lng": 103.8925,
        },
        {
            "type": POIType.SUPERMARKET,
            "name": "NTUC FairPrice Tampines Mall",
            "lat": 1.3525,
            "lng": 103.9455,
        },
        # Clinics
        {"type": POIType.CLINIC, "name": "Healthway Medical AMK", "lat": 1.3685, "lng": 103.8465},
        {"type": POIType.CLINIC, "name": "My Family Clinic Bedok", "lat": 1.3295, "lng": 103.9285},
        {"type": POIType.CLINIC, "name": "Clementi Clinic", "lat": 1.3148, "lng": 103.7650},
        {"type": POIType.CLINIC, "name": "Hougang Polyclinic", "lat": 1.3720, "lng": 103.8945},
        {"type": POIType.CLINIC, "name": "Tampines Polyclinic", "lat": 1.3510, "lng": 103.9430},
        # Parks
        {"type": POIType.PARK, "name": "Bishan-Ang Mo Kio Park", "lat": 1.3650, "lng": 103.8500},
        {"type": POIType.PARK, "name": "Bedok Reservoir Park", "lat": 1.3360, "lng": 103.9230},
        {"type": POIType.PARK, "name": "Clementi Woods Park", "lat": 1.3200, "lng": 103.7710},
        {"type": POIType.PARK, "name": "Hougang Park", "lat": 1.3740, "lng": 103.8880},
        {"type": POIType.PARK, "name": "Tampines Eco Green", "lat": 1.3570, "lng": 103.9380},
        # Malls/Hawkers
        {"type": POIType.MALL, "name": "AMK Hub", "lat": 1.3695, "lng": 103.8490},
        {"type": POIType.MALL, "name": "Bedok Mall", "lat": 1.3245, "lng": 103.9295},
        {"type": POIType.MALL, "name": "Clementi Mall", "lat": 1.3152, "lng": 103.7647},
        {
            "type": POIType.HAWKER,
            "name": "Hougang 1 Market & Food Centre",
            "lat": 1.3705,
            "lng": 103.8915,
        },
        {"type": POIType.MALL, "name": "Tampines 1", "lat": 1.3535, "lng": 103.9445},
    ]

    pois = []
    for data in pois_data:
        poi = POI(
            poi_type=data["type"],
            name=data["name"],
            latitude=data["lat"],
            longitude=data["lng"],
            last_updated=datetime.utcnow(),
        )
        pois.append(poi)

    session.add_all(pois)
    session.commit()
    for poi in pois:
        session.refresh(poi)
    print(f"✅ Created {len(pois)} POIs")
    return pois


def seed_transactions(
    session: Session, blocks: list[Block], ingestion_run: IngestionRun
) -> list[Transaction]:
    """Create transaction records."""
    transactions = []
    flat_types = ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM"]
    storey_ranges = ["01 TO 03", "04 TO 06", "07 TO 09", "10 TO 12", "13 TO 15"]
    flat_models = ["Improved", "New Generation", "Model A", "Premium Apartment", "Simplified"]

    # Generate 100 transactions across the blocks
    start_date = date.today() - timedelta(days=730)  # Last 24 months

    for _ in range(100):
        block = random.choice(blocks)
        flat_type = random.choice(flat_types)

        # Generate realistic prices based on flat type
        base_prices = {
            "2 ROOM": (200000, 300000),
            "3 ROOM": (300000, 450000),
            "4 ROOM": (450000, 650000),
            "5 ROOM": (600000, 850000),
        }
        min_price, max_price = base_prices[flat_type]
        price = random.uniform(min_price, max_price)

        # Floor area based on flat type
        floor_areas = {
            "2 ROOM": (45, 55),
            "3 ROOM": (60, 75),
            "4 ROOM": (85, 105),
            "5 ROOM": (110, 130),
        }
        min_area, max_area = floor_areas[flat_type]
        floor_area = random.uniform(min_area, max_area)

        # Random date within last 24 months
        days_offset = random.randint(0, 730)
        transaction_date = start_date + timedelta(days=days_offset)

        transaction = Transaction(
            date=transaction_date,
            block=block.block,
            street=block.street,
            flat_type=flat_type,
            storey_range=random.choice(storey_ranges),
            floor_area_sqm=round(floor_area, 2),
            price=round(price, 2),
            lease_commence_date=block.lease_commence_year or 1980,
            town=block.town,
            flat_model=random.choice(flat_models),
            latitude=block.latitude,
            longitude=block.longitude,
            ingestion_run_id=ingestion_run.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        transactions.append(transaction)

    session.add_all(transactions)
    session.commit()
    print(f"✅ Created {len(transactions)} transactions")
    return transactions


def seed_leads(session: Session) -> list[Lead]:
    """Create lead records."""
    leads_data = [
        {
            "name": "John Tan",
            "email": "john.tan@example.com",
            "mobile": "+65 9123 4567",
            "contact_window": "Weekdays 6-9pm",
            "budget_range": "400k-500k",
            "preferred_towns": ["Ang Mo Kio", "Hougang"],
            "flat_types": ["3 ROOM", "4 ROOM"],
            "timeline": "Within 3 months",
            "first_timer": True,
            "financing_status": "Pre-approved",
            "notes": "Looking for quiet neighborhood",
            "status": LeadStatus.NEW,
        },
        {
            "name": "Sarah Lim",
            "email": "sarah.lim@example.com",
            "mobile": "+65 8234 5678",
            "contact_window": "Weekends anytime",
            "budget_range": "500k-600k",
            "preferred_towns": ["Bedok", "Tampines"],
            "flat_types": ["4 ROOM", "5 ROOM"],
            "timeline": "6-12 months",
            "first_timer": False,
            "financing_status": "Need help",
            "notes": "Upgrading from 3-room",
            "status": LeadStatus.NEW,
        },
        {
            "name": "David Wong",
            "email": "david.wong@example.com",
            "mobile": "+65 9345 6789",
            "contact_window": "Anytime",
            "budget_range": "600k+",
            "preferred_towns": ["Clementi"],
            "flat_types": ["5 ROOM"],
            "timeline": "Within 3 months",
            "first_timer": False,
            "financing_status": "Cash buyer",
            "notes": "Near MRT preferred",
            "status": LeadStatus.CONTACTED,
        },
        {
            "name": "Emily Chua",
            "email": "emily.chua@example.com",
            "mobile": "+65 8456 7890",
            "contact_window": "Weekdays 12-2pm",
            "budget_range": "300k-400k",
            "preferred_towns": ["Ang Mo Kio", "Bedok"],
            "flat_types": ["2 ROOM", "3 ROOM"],
            "timeline": "Flexible",
            "first_timer": True,
            "financing_status": "Pre-approved",
            "notes": "First-time buyer",
            "status": LeadStatus.NEW,
        },
        {
            "name": "Michael Ng",
            "email": "michael.ng@example.com",
            "mobile": "+65 9567 8901",
            "contact_window": "Weekends only",
            "budget_range": "450k-550k",
            "preferred_towns": ["Hougang", "Tampines"],
            "flat_types": ["4 ROOM"],
            "timeline": "Within 6 months",
            "first_timer": False,
            "financing_status": "Pre-approved",
            "notes": "Family of 4",
            "status": LeadStatus.CONTACTED,
        },
        {
            "name": "Rachel Teo",
            "email": "rachel.teo@example.com",
            "mobile": "+65 8678 9012",
            "budget_range": "500k+",
            "preferred_towns": ["Clementi"],
            "flat_types": ["4 ROOM", "5 ROOM"],
            "timeline": "Within 3 months",
            "first_timer": False,
            "status": LeadStatus.CLOSED,
        },
        {
            "name": "Benjamin Lee",
            "email": "benjamin.lee@example.com",
            "mobile": "+65 9789 0123",
            "contact_window": "After 7pm",
            "budget_range": "350k-450k",
            "preferred_towns": ["Ang Mo Kio"],
            "flat_types": ["3 ROOM"],
            "timeline": "Flexible",
            "first_timer": True,
            "financing_status": "Need help",
            "notes": "Young couple",
            "status": LeadStatus.NEW,
        },
        {
            "name": "Amanda Koh",
            "email": "amanda.koh@example.com",
            "mobile": "+65 8890 1234",
            "contact_window": "Weekdays 9-5pm",
            "budget_range": "550k-650k",
            "preferred_towns": ["Bedok", "Tampines"],
            "flat_types": ["5 ROOM"],
            "timeline": "6-12 months",
            "first_timer": False,
            "financing_status": "Cash buyer",
            "status": LeadStatus.CONTACTED,
        },
        {
            "name": "Jason Ong",
            "email": "jason.ong@example.com",
            "mobile": "+65 9901 2345",
            "budget_range": "400k-500k",
            "preferred_towns": ["Hougang"],
            "flat_types": ["3 ROOM", "4 ROOM"],
            "timeline": "Within 3 months",
            "first_timer": True,
            "status": LeadStatus.NEW,
        },
        {
            "name": "Michelle Tan",
            "email": "michelle.tan@example.com",
            "mobile": "+65 8012 3456",
            "contact_window": "Weekends preferred",
            "budget_range": "600k+",
            "preferred_towns": ["Clementi"],
            "flat_types": ["5 ROOM"],
            "timeline": "Flexible",
            "first_timer": False,
            "financing_status": "Pre-approved",
            "notes": "Near good schools",
            "status": LeadStatus.CLOSED,
        },
    ]

    leads = []
    for _, data in enumerate(leads_data):
        # Add some variation in created_at timestamps
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        lead = Lead(
            name=data["name"],
            email=data["email"],
            mobile=data["mobile"],
            contact_window=data.get("contact_window"),
            budget_range=data.get("budget_range"),
            preferred_towns=data.get("preferred_towns", []),
            flat_types=data.get("flat_types", []),
            timeline=data.get("timeline"),
            first_timer=data.get("first_timer", False),
            financing_status=data.get("financing_status"),
            notes=data.get("notes"),
            filter_snapshot=None,
            shortlist_snapshot=None,
            created_at=created_at,
            updated_at=created_at,
            status=data["status"],
        )
        leads.append(lead)

    session.add_all(leads)
    session.commit()
    print(f"✅ Created {len(leads)} leads")
    return leads


def main():
    """Main seed function."""
    print("🌱 Starting database seed...")

    # Create tables
    create_tables()

    # Create session
    session = SessionLocal()

    try:
        # Seed data in order (respecting foreign key dependencies)
        ingestion_runs = seed_ingestion_runs(session)
        blocks = seed_blocks(session)
        pois = seed_pois(session)
        transactions = seed_transactions(session, blocks, ingestion_runs[0])
        leads = seed_leads(session)

        print("\n✅ Database seeded successfully!")
        print(f"   - {len(ingestion_runs)} ingestion runs")
        print(f"   - {len(blocks)} blocks")
        print(f"   - {len(pois)} POIs")
        print(f"   - {len(transactions)} transactions")
        print(f"   - {len(leads)} leads")
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
