from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError


@dataclass
class IngestResult:
    raw_id: str
    ingested_at: datetime
    idempotent: bool



def _hash_payload(payload: dict) -> str:
    payload_bytes = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(payload_bytes).hexdigest()



def record_request_audit(
    db: Session,
    *,
    request_id: str,
    source_id: str,
    external_id: str,
    status: str,
    error_code: str | None = None,
    message: str | None = None,
) -> None:
    db.execute(
        text(
            """
            insert into app.request_audit (
              request_id,
              source_id,
              external_id,
              received_at,
              status,
              error_code,
              message
            ) values (
              cast(:request_id as uuid),
              :source_id,
              :external_id,
              now(),
              :status,
              :error_code,
              :message
            )
            on conflict (request_id) do update
            set status = excluded.status,
                error_code = excluded.error_code,
                message = excluded.message;
            """
        ),
        {
            "request_id": request_id,
            "source_id": source_id,
            "external_id": external_id,
            "status": status,
            "error_code": error_code,
            "message": message,
        },
    )



def ingest_signal(
    db: Session,
    *,
    request_id: str,
    source_id: str,
    external_id: str,
    occurred_at: datetime,
    payload: dict,
) -> IngestResult:
    payload_hash = _hash_payload(payload)

    try:
        existing = db.execute(
            text(
                """
                select raw_id, occurred_at, payload_json, payload_hash, ingested_at
                from raw.raw_event
                where source_id = :source_id and external_id = :external_id
                """
            ),
            {"source_id": source_id, "external_id": external_id},
        ).mappings().first()

        if existing:
            existing_payload_hash = existing["payload_hash"]
            if existing_payload_hash != payload_hash or existing["occurred_at"] != occurred_at:
                raise AppError(
                    code="DUPLICATE_IDEMPOTENCY_KEY",
                    message="source_id + external_id already exists with different payload",
                    http_status=409,
                    request_id=request_id,
                )

            record_request_audit(
                db,
                request_id=request_id,
                source_id=source_id,
                external_id=external_id,
                status="ok",
            )
            db.commit()
            return IngestResult(
                raw_id=str(existing["raw_id"]),
                ingested_at=existing["ingested_at"],
                idempotent=True,
            )

        inserted = db.execute(
            text(
                """
                insert into raw.raw_event (
                  source_id,
                  external_id,
                  occurred_at,
                  payload_json,
                  payload_hash,
                  request_id
                ) values (
                  :source_id,
                  :external_id,
                  :occurred_at,
                  cast(:payload_json as jsonb),
                  :payload_hash,
                  cast(:request_id as uuid)
                )
                returning raw_id, ingested_at;
                """
            ),
            {
                "source_id": source_id,
                "external_id": external_id,
                "occurred_at": occurred_at.astimezone(UTC),
                "payload_json": json.dumps(payload, ensure_ascii=True),
                "payload_hash": payload_hash,
                "request_id": request_id,
            },
        ).mappings().one()

        record_request_audit(
            db,
            request_id=request_id,
            source_id=source_id,
            external_id=external_id,
            status="ok",
        )
        db.commit()
        return IngestResult(
            raw_id=str(inserted["raw_id"]),
            ingested_at=inserted["ingested_at"],
            idempotent=False,
        )

    except AppError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppError(
            code="RAW_WRITE_FAILED",
            message=f"failed to write raw event: {exc}",
            http_status=500,
            request_id=request_id,
        ) from exc



def register_ingest_error(
    db: Session,
    *,
    request_id: str,
    source_id: str,
    external_id: str,
    code: str,
    message: str,
) -> None:
    record_request_audit(
        db,
        request_id=request_id,
        source_id=source_id,
        external_id=external_id,
        status="error",
        error_code=code,
        message=message,
    )
    db.commit()
