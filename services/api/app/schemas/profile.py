from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


class ProfileUpsertRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=64)
    gender: str | None = Field(default=None, max_length=32)
    birth_date: date | None = None
    height_cm: float | None = Field(default=None, ge=30, le=300)
    weight_kg: float | None = Field(default=None, ge=1, le=700)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name cannot be empty")
        return normalized

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        normalized = value.strip()
        try:
            ZoneInfo(normalized)
        except Exception as exc:
            raise ValueError("invalid timezone") from exc
        return normalized


class ProfileResponse(BaseModel):
    user_id: str
    display_name: str
    timezone: str
    gender: str | None
    birth_date: date | None
    height_cm: float | None
    weight_kg: float | None
    profile_completed: bool
