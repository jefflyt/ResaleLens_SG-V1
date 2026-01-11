"""Application configuration management."""

import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env.local (for actual secrets) with fallback to .env
# .env.local is git-ignored and should contain real API keys
# .env.example is a template (committed to git)
load_dotenv(".env.local")  # Load .env.local first (if exists)
load_dotenv()  # Fallback to .env if .env.local doesn't exist


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        # DATABASE_URL is required - no SQLite fallback
        self.database_url: str | None = os.getenv("DATABASE_URL")

        if not self.database_url:
            print("\n❌ ERROR: DATABASE_URL environment variable is required")
            print("\n📝 To fix:")
            print("   1. Copy .env.example to .env.local")
            print("   2. Set DATABASE_URL to your Supabase connection string")
            print("   3. See docs/technical/supabase_setup.md for help")
            print("\nExample:")
            print("   DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres\n")
            sys.exit(1)

        # Validate it's a PostgreSQL URL
        if not self.database_url.startswith("postgresql://"):
            print("\n❌ ERROR: DATABASE_URL must be a PostgreSQL connection string")
            print(f"   Got: {self.database_url[:50]}...")
            print("\n📝 Expected format:")
            print("   postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
            print("\n   See docs/technical/supabase_setup.md for setup guide\n")
            sys.exit(1)

        self.env: str = os.getenv("ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        self.secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))


# Singleton settings instance
settings = Settings()
