"""Application configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env.local (for actual secrets) with fallback to .env
# .env.local is git-ignored and should contain real API keys
# .env.example is a template (committed to git)
load_dotenv(".env.local")  # Load .env.local first (if exists)
load_dotenv()  # Fallback to .env if .env.local doesn't exist


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/resalelens.db")
        self.env: str = os.getenv("ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        self.secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        # Ensure data directory exists
        self._ensure_data_directory()

    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists for SQLite databases."""
        if self.database_url.startswith("sqlite"):
            # Extract path from SQLite URL
            db_path = self.database_url.replace("sqlite:///", "")
            data_dir = Path(db_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)


# Singleton settings instance
settings = Settings()
