from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError



def create_annotation(
    db: Session,
    *,
    target_type: str,
    target_id: str,
    label: str,
    value: str,
) -> tuple[str, str]:
    try:
        target_exists = db.execute(
            text(
                """
                select exists(
                    select 1
                    from domain_poc_signal.signal_event
                    where signal_event_id = :target_id::uuid
                ) as has_target;
                """
            ),
            {"target_id": target_id},
        ).scalar_one()
    except ProgrammingError as exc:
        db.rollback()
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message="domain_poc_signal.signal_event is not available yet",
            http_status=503,
        ) from exc

    if not target_exists:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="target_id does not exist in domain_poc_signal.signal_event",
            http_status=400,
        )

    try:
        inserted = db.execute(
            text(
                """
                insert into annotation.annotation (
                  target_type,
                  target_id,
                  label,
                  value
                ) values (
                  :target_type,
                  :target_id::uuid,
                  :label,
                  :value
                ) returning annotation_id, created_at;
                """
            ),
            {
                "target_type": target_type,
                "target_id": target_id,
                "label": label,
                "value": value,
            },
        ).mappings().one()
        db.commit()
        return str(inserted["annotation_id"]), inserted["created_at"].isoformat()
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppError(
            code="INTERNAL_ERROR",
            message=f"failed to create annotation: {exc}",
            http_status=500,
        ) from exc
