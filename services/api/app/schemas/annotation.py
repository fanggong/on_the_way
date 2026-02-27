from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnnotationCreateRequest(BaseModel):
    target_type: Literal["health_event", "health_activity_event"]
    target_id: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=256)


class AnnotationCreateResponse(BaseModel):
    status: Literal["ok"]
    annotation_id: str
    created_at: datetime
