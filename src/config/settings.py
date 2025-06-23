import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "online_cinema.db")
    PATH_TO_MOVIES_CSV: str = str(BASE_DIR / "database" / "seed_data" / "imdb_movies.csv")

    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(BASE_DIR / "notifications" / "templates")

    LOGIN_TIME_DAYS: int = 7

    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "host")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", 25))
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "testuser")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "test_password")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
    MAILHOG_API_PORT: int = int(os.getenv("MAILHOG_API_PORT", 8025))

    DROPBOX_ACCESS_TOKEN: str = os.getenv("DROPBOX_ACCESS_TOKEN", "dropbox_access_token")
    DROPBOX_REFRESH_TOKEN: str = os.getenv("DROPBOX_REFRESH_TOKEN", "dropbox_refresh_token")
    DROPBOX_APP_KEY: str = os.getenv("DROPBOX_APP_KEY", "dropbox_app_key")
    DROPBOX_APP_SECRET: str = os.getenv("DROPBOX_APP_SECRET", "dropbox_app_secret")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "test_secret_key")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "test_publishable_key")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "test_webhook_secret")
    STRIPE_CURRENCY: str = os.getenv("STRIPE_CURRENCY", "usd")


class Settings(BaseAppSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "test_host")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", os.urandom(32).hex())
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", os.urandom(32).hex())
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"


class TestingSettings(BaseAppSettings):
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(self, "PATH_TO_MOVIES_CSV", str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv"))
