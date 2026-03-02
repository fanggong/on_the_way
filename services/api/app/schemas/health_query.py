from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

_ALLOWED_CONFIG_KEYS = {
    "GARMIN_FETCH_WINDOW_DAYS",
    "GARMIN_BACKFILL_DAYS",
    "GARMIN_TIMEZONE",
    "GARMIN_IS_CN",
}


class HealthConnectorConfigUpdateRequest(BaseModel):
    GARMIN_FETCH_WINDOW_DAYS: int = Field(ge=1, le=90)
    GARMIN_BACKFILL_DAYS: int = Field(ge=1, le=180)
    GARMIN_TIMEZONE: str = Field(min_length=1, max_length=64)
    GARMIN_IS_CN: bool

    @field_validator("GARMIN_TIMEZONE")
    @classmethod
    def normalize_timezone(cls, value: str) -> str:
        return value.strip()


class HealthDomainQueryParams(BaseModel):
    start_date: str
    end_date: str
    metric_name: str | None = None
    account_ref: str | None = None
    page: int = Field(default=1, ge=1, le=100000)
    page_size: int = Field(default=20, ge=1, le=200)


class HealthMartPagination(BaseModel):
    page: int = Field(default=1, ge=1, le=100000)
    page_size: int = Field(default=20, ge=1, le=200)
