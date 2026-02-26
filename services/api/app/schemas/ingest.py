from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


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
        if value.tzinfo is None:
            raise ValueError("occurred_at must include timezone")
        max_time = datetime.now(UTC) + timedelta(
            minutes=settings.request_future_tolerance_minutes
        )
        if value > max_time:
            raise ValueError("occurred_at is too far in the future")
        return value


class ConnectorSignalIngestRequest(BaseModel):
    source_id: Literal["signal_random_connector"]
    external_id: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    payload: ConnectorSignalPayload

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must include timezone")
        max_time = datetime.now(UTC) + timedelta(
            minutes=settings.request_future_tolerance_minutes
        )
        if value > max_time:
            raise ValueError("occurred_at is too far in the future")
        return value


class IngestResponse(BaseModel):
    status: Literal["ok"]
    raw_id: str
    ingested_at: datetime
    idempotent: bool
