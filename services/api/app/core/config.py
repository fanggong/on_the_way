from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    request_future_tolerance_minutes: int
    garmin_email: str
    cors_allow_origins: List[str]
    jwt_secret: str
    access_token_expires_minutes: int
    refresh_token_expires_days: int
    refresh_cookie_name: str
    auth_rate_limit_per_minute: int


def _split_csv(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "on_the_way-api"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://otw:otw_dev_password@postgres:5432/otw_dev",
        ),
        request_future_tolerance_minutes=int(
            os.getenv("REQUEST_FUTURE_TOLERANCE_MINUTES", "5")
        ),
        garmin_email=os.getenv("GARMIN_EMAIL", "").strip(),
        cors_allow_origins=_split_csv(
            os.getenv(
                "CORS_ALLOW_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        ),
        jwt_secret=os.getenv("AUTH_JWT_SECRET", "otw-dev-secret-change-me"),
        access_token_expires_minutes=int(
            os.getenv("AUTH_ACCESS_EXPIRES_MINUTES", "30")
        ),
        refresh_token_expires_days=int(os.getenv("AUTH_REFRESH_EXPIRES_DAYS", "7")),
        refresh_cookie_name=os.getenv("AUTH_REFRESH_COOKIE_NAME", "otw_refresh_token"),
        auth_rate_limit_per_minute=int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "30")),
    )


settings = load_settings()
