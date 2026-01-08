"""Database setup script for initial database creation."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resalelens.database import Base, engine
from src.resalelens.models import LeadRequest, User  # noqa: F401


def setup_database() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print(f"✓ Database location: {engine.url}")


if __name__ == "__main__":
    setup_database()
