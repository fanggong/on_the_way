from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorSettings:
    api_base_url: str
    ingest_path: str
    interval_seconds: int
    source_id: str
    generator_version: str
    request_timeout_seconds: int
    retry_attempts: int
    db_url: str



def normalize_db_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)



def load_settings() -> ConnectorSettings:
    raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://otw:otw_dev_password@postgres:5432/otw_dev",
    )
    return ConnectorSettings(
        api_base_url=os.getenv("API_BASE_URL", "http://api-service:8000"),
        ingest_path=os.getenv("CONNECTOR_INGEST_PATH", "/v1/ingest/connector-signal"),
        interval_seconds=int(os.getenv("CONNECTOR_INTERVAL_SECONDS", "300")),
        source_id=os.getenv("CONNECTOR_SOURCE_ID", "signal_random_connector"),
        generator_version=os.getenv("CONNECTOR_GENERATOR_VERSION", "v1"),
        request_timeout_seconds=int(os.getenv("CONNECTOR_REQUEST_TIMEOUT_SECONDS", "10")),
        retry_attempts=int(os.getenv("CONNECTOR_RETRY_ATTEMPTS", "3")),
        db_url=normalize_db_url(raw_db_url),
    )


settings = load_settings()
