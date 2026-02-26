from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings

HEALTH_ALLOWED_TIMEZONE = "Asia/Shanghai"
_SHANGHAI_TZ = ZoneInfo(HEALTH_ALLOWED_TIMEZONE)
HEALTH_ALLOWED_METRIC_TYPES = {
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
}


def _validate_occurred_at(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("occurred_at must include timezone")
    max_time = datetime.now(UTC) + timedelta(
        minutes=settings.request_future_tolerance_minutes
    )
    if value > max_time:
        raise ValueError("occurred_at is too far in the future")
    return value


def _validate_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return value


def _validate_shanghai_offset(value: datetime, *, field_name: str) -> datetime:
    expected_offset = datetime.now(_SHANGHAI_TZ).utcoffset()
    if value.utcoffset() != expected_offset:
        raise ValueError(f"{field_name} must use Asia/Shanghai offset")
    return value


class ManualSignalPayload(BaseModel):
    value: float = Field(ge=0, le=100)
    note: str | None = Field(default=None, max_length=256)


class ConnectorSignalPayload(BaseModel):
    value: float = Field(ge=0, le=100)
    seed: str = Field(min_length=1, max_length=64)
    generator_version: str = Field(min_length=1, max_length=32)


class ManualSignalIngestRequest(BaseModel):
    source_id: Literal["ios_manual"]
    external_id: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    payload: ManualSignalPayload

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        return _validate_occurred_at(value)


class ConnectorSignalIngestRequest(BaseModel):
    source_id: Literal["signal_random_connector"]
    external_id: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    payload: ConnectorSignalPayload

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        return _validate_occurred_at(value)


class HealthConnectorPayload(BaseModel):
    connector: Literal["garmin_connect"]
    connector_version: str = Field(min_length=1, max_length=32)
    account_ref: str = Field(min_length=1, max_length=64)
    metric_type: str = Field(min_length=1, max_length=64)
    metric_date: date
    timezone: Literal[HEALTH_ALLOWED_TIMEZONE]
    fetched_at: datetime
    api_method: str | None = Field(default=None, min_length=1, max_length=128)
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metric_type")
    @classmethod
    def validate_metric_type(cls, value: str) -> str:
        if value not in HEALTH_ALLOWED_METRIC_TYPES:
            raise ValueError("unsupported metric_type")
        return value

    @field_validator("fetched_at")
    @classmethod
    def validate_fetched_at(cls, value: datetime) -> datetime:
        value = _validate_timezone_aware(value, field_name="fetched_at")
        return _validate_shanghai_offset(value, field_name="fetched_at")


class HealthConnectorIngestRequest(BaseModel):
    source_id: Literal["garmin_connect_health"]
    external_id: str = Field(min_length=1, max_length=128)
    occurred_at: datetime
    payload: HealthConnectorPayload

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        value = _validate_occurred_at(value)
        return _validate_shanghai_offset(value, field_name="occurred_at")

    @model_validator(mode="after")
    def validate_occurred_metric_alignment(self) -> HealthConnectorIngestRequest:
        metric_timezone = _SHANGHAI_TZ
        expected_occurred_at = datetime.combine(
            self.payload.metric_date,
            time.min,
            tzinfo=metric_timezone,
        )
        if self.occurred_at.astimezone(metric_timezone) != expected_occurred_at:
            raise ValueError(
                "occurred_at must equal metric_date 00:00:00 in Asia/Shanghai"
            )
        return self


class IngestResponse(BaseModel):
    status: Literal["ok"]
    raw_id: str
    ingested_at: datetime
    idempotent: bool
