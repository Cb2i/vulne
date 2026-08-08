"""Application configuration, loaded from environment variables / .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VULNASSIST_", extra="ignore")

    app_name: str = "VulnAssist"
    environment: str = "development"

    # Database: defaults to a local SQLite file under <project_root>/data.
    # For PostgreSQL, set VULNASSIST_DATABASE_URL, e.g.
    # postgresql+psycopg2://user:password@localhost:5432/vulnassist
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'vulnassist.db').as_posix()}"

    # JWT auth
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_" + "0" * 32
    access_token_expire_minutes: int = 60 * 8  # 8h working session
    jwt_algorithm: str = "HS256"

    # CORS - only needed when running the Vite dev server separately.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Static frontend (built assets) served directly by FastAPI in production.
    frontend_dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"

    # Default admin bootstrap (only used by the seed script, disabled once users exist)
    default_admin_email: str = "admin@vulnassist.internal"
    default_admin_password: str = "ChangeMe123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()
