from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings:
    environment: str
    database_url: str
    frontend_origins: list[str]
    max_request_bytes: int
    rate_limit_per_minute: int
    rate_limit_write_per_minute: int
    api_key: str | None

    def __init__(self) -> None:
        self.environment = os.getenv("APP_ENV", "development").lower()
        default_db = f"sqlite:///{PROJECT_ROOT / 'backend' / 'database' / 'infraguard.db'}"
        self.database_url = os.getenv("DATABASE_URL", default_db)
        configured_origins = os.getenv("FRONTEND_ORIGINS")
        if configured_origins:
            self.frontend_origins = [
                origin.strip() for origin in configured_origins.split(",") if origin.strip()
            ]
        elif self.environment == "production":
            self.frontend_origins = ["http://localhost:5174"]
        else:
            self.frontend_origins = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5174",
            ]

        self.max_request_bytes = int(os.getenv("MAX_REQUEST_BYTES", "1048576"))
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.rate_limit_write_per_minute = int(os.getenv("RATE_LIMIT_WRITE_PER_MINUTE", "10"))
        self.api_key = os.getenv("API_KEY") or None

    @property
    def production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
