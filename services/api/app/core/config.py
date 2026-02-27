from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    request_future_tolerance_minutes: int
    garmin_email: str


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
    )


settings = load_settings()
