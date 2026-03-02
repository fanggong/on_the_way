from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CoreSourceUpdateRequest(BaseModel):
    connector_code: str = Field(min_length=1, max_length=64)


class ConnectorEnableRequest(BaseModel):
    enabled: bool


class SyncPolicyUpdateRequest(BaseModel):
    auto_sync_enabled: bool
    auto_sync_interval_minutes: int = Field(ge=15, le=1440)


class SyncJobCreateRequest(BaseModel):
    job_type: str
    backfill_start_at: datetime
    backfill_end_at: datetime

    @model_validator(mode="after")
    def validate_job(self) -> "SyncJobCreateRequest":
        if self.job_type != "backfill_once":
            raise ValueError("job_type must be backfill_once")
        if self.backfill_start_at.tzinfo is None or self.backfill_end_at.tzinfo is None:
            raise ValueError("backfill range must include timezone")
        if self.backfill_start_at > self.backfill_end_at:
            raise ValueError("backfill_start_at must be <= backfill_end_at")
        return self
