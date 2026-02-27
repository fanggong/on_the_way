from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import DataError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError

TARGET_EXISTS_SQL = {
    "health_event": """
        select exists(
            select 1
            from canonical.health_event
            where health_event_id = cast(:target_id as uuid)
        ) as has_target;
    """,
    "health_activity_event": """
        select exists(
            select 1
            from canonical.health_activity_event
            where activity_event_id = :target_id
        ) as has_target;
    """,
}


def create_annotation(
    db: Session,
    *,
    target_type: str,
    target_id: str,
    label: str,
    value: str,
) -> tuple[str, str]:
    exists_sql = TARGET_EXISTS_SQL.get(target_type)
    if exists_sql is None:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="unsupported target_type",
            http_status=400,
        )

    try:
        target_exists = db.execute(
            text(exists_sql),
            {"target_id": target_id},
        ).scalar_one()
    except DataError as exc:
        db.rollback()
        raise AppError(
            code="INVALID_ARGUMENT",
            message="target_id format is invalid for target_type",
            http_status=400,
        ) from exc
    except ProgrammingError as exc:
        db.rollback()
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message="canonical health models are unavailable, run dbt build first",
            http_status=503,
        ) from exc

    if not target_exists:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="target_id does not exist in canonical health models",
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
                  :target_id,
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
