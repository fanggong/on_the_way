from __future__ import annotations

from datetime import UTC, datetime, date
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.annotation import AnnotationCreateRequest
from app.schemas.ingest import (
    ConnectorSignalIngestRequest,
    IngestResponse,
    ManualSignalIngestRequest,
)
from app.services.annotation_service import create_annotation
from app.services.ingest_service import ingest_signal, register_ingest_error
from app.services.query_service import (
    get_connector_health,
    get_daily_summary,
    get_signals,
)

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health/live")
def health_live() -> dict:
    return {
        "status": "ok",
        "service": "api-service",
        "time": datetime.now(UTC).isoformat(),
    }


@router.get("/health/connector")
def health_connector(db: Session = Depends(get_db)) -> dict:
    health = get_connector_health(db)
    return {"status": "ok", **health}


@router.post("/ingest/manual-signal", response_model=IngestResponse)
def ingest_manual_signal(
    body: ManualSignalIngestRequest,
    db: Session = Depends(get_db),
) -> dict:
    request_id = str(uuid4())
    try:
        result = ingest_signal(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            occurred_at=body.occurred_at,
            payload=body.payload.model_dump(mode="json"),
        )
        return {
            "status": "ok",
            "raw_id": result.raw_id,
            "ingested_at": result.ingested_at,
            "idempotent": result.idempotent,
        }
    except AppError as exc:
        register_ingest_error(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            code=exc.code,
            message=exc.message,
        )
        exc.request_id = request_id
        raise


@router.post("/ingest/connector-signal", response_model=IngestResponse)
def ingest_connector_signal(
    body: ConnectorSignalIngestRequest,
    db: Session = Depends(get_db),
) -> dict:
    request_id = str(uuid4())
    try:
        result = ingest_signal(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            occurred_at=body.occurred_at,
            payload=body.payload.model_dump(mode="json"),
        )
        return {
            "status": "ok",
            "raw_id": result.raw_id,
            "ingested_at": result.ingested_at,
            "idempotent": result.idempotent,
        }
    except AppError as exc:
        register_ingest_error(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            code=exc.code,
            message=exc.message,
        )
        exc.request_id = request_id
        raise


@router.post("/annotation")
def post_annotation(
    body: AnnotationCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    annotation_id, created_at = create_annotation(
        db,
        target_type=body.target_type,
        target_id=body.target_id,
        label=body.label,
        value=body.value,
    )
    return {
        "status": "ok",
        "annotation_id": annotation_id,
        "created_at": created_at,
    }


@router.get("/poc/signals")
def list_signals(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    items = get_signals(db, limit=limit)
    return {
        "status": "ok",
        "items": items,
    }


@router.get("/poc/daily-summary")
def daily_summary(
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
) -> dict:
    summary = get_daily_summary(db, stat_date=date_value)
    return {
        "status": "ok",
        **summary,
    }
