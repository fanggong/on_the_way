from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_METRICS = (
    "user_summary",
    "sleep",
    "heart_rate",
    "resting_heart_rate",
    "stress",
    "body_battery",
    "respiration",
    "spo2",
    "hrv",
    "intensity_minutes",
    "weight",
    "body_composition",
    "hydration",
    "blood_pressure",
    "menstrual",
    "pregnancy",
    "activities",
    "training_status",
    "training_readiness",
    "recovery_time",
    "max_metrics_vo2",
    "race_prediction",
    "hill_score",
    "endurance_score",
    "lactate_threshold",
    "workouts",
    "training_plans",
    "devices",
    "gear",
    "goals",
    "badges",
    "challenges",
)


@dataclass(frozen=True)
class ConnectorSettings:
    api_base_url: str
    ingest_path: str
    interval_seconds: int
    source_id: str
    connector_version: str
    request_timeout_seconds: int
    retry_attempts: int
    db_url: str
    garmin_email: str
    garmin_password: str
    garmin_token_dir: str
    garmin_fetch_window_days: int
    garmin_backfill_days: int
    garmin_metrics: tuple[str, ...]
    garmin_timezone: str
    garmin_is_cn: bool
    garmin_mfa_code: str | None


def normalize_db_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _positive_int_env(name: str, default: str) -> int:
    value = int(os.getenv(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


def _parse_metrics(raw_value: str) -> tuple[str, ...]:
    normalized = raw_value.strip().lower()
    if normalized == "all":
        return DEFAULT_METRICS

    items = [part.strip() for part in raw_value.split(",") if part.strip()]
    if not items:
        return DEFAULT_METRICS

    deduplicated: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            deduplicated.append(item)
            seen.add(item)
    return tuple(deduplicated)


def _parse_bool_env(name: str, default: str) -> bool:
    raw = os.getenv(name, default).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def load_settings() -> ConnectorSettings:
    raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://otw:otw_dev_password@postgres:5432/otw_dev",
    )
    return ConnectorSettings(
        api_base_url=os.getenv("API_BASE_URL", "http://api-service:8000"),
        ingest_path=os.getenv("CONNECTOR_INGEST_PATH", "/v1/ingest/connector-health"),
        interval_seconds=_positive_int_env("CONNECTOR_INTERVAL_SECONDS", "3600"),
        source_id="garmin_connect_health",
        connector_version=os.getenv("CONNECTOR_VERSION", "v0.3.1"),
        request_timeout_seconds=_positive_int_env(
            "CONNECTOR_REQUEST_TIMEOUT_SECONDS", "10"
        ),
        retry_attempts=_positive_int_env("CONNECTOR_RETRY_ATTEMPTS", "3"),
        db_url=normalize_db_url(raw_db_url),
        garmin_email=os.getenv("GARMIN_EMAIL", "").strip(),
        garmin_password=os.getenv("GARMIN_PASSWORD", "").strip(),
        garmin_token_dir=os.getenv("GARMIN_TOKEN_DIR", "/tmp/.garminconnect"),
        garmin_fetch_window_days=_positive_int_env("GARMIN_FETCH_WINDOW_DAYS", "3"),
        garmin_backfill_days=_positive_int_env("GARMIN_BACKFILL_DAYS", "10"),
        garmin_metrics=_parse_metrics(os.getenv("GARMIN_METRICS", "all")),
        garmin_timezone=os.getenv("GARMIN_TIMEZONE", "Asia/Shanghai"),
        garmin_is_cn=_parse_bool_env("GARMIN_IS_CN", "true"),
        garmin_mfa_code=os.getenv("GARMIN_MFA_CODE"),
    )


settings = load_settings()
