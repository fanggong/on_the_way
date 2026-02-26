from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.core.errors import AppError


def get_signals(db: Session, *, limit: int = 50) -> list[dict]:
    try:
        rows = db.execute(
            text(
                """
                select
                  signal_event_id,
                  event_id,
                  source_type,
                  value_num,
                  occurred_at,
                  is_valid,
                  coalesce(tags_json, '{}'::jsonb) as tags_json
                from domain_poc_signal.signal_event
                order by occurred_at desc
                limit :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
    except ProgrammingError as exc:
        db.rollback()
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message="domain model is unavailable, run dbt build first",
            http_status=503,
        ) from exc

    return [
        {
            "signal_event_id": str(row["signal_event_id"]),
            "event_id": str(row["event_id"]),
            "source_type": row["source_type"],
            "value_num": float(row["value_num"]),
            "occurred_at": row["occurred_at"],
            "is_valid": bool(row["is_valid"]),
            "tags_json": row["tags_json"],
        }
        for row in rows
    ]


def get_daily_summary(db: Session, *, stat_date: date) -> dict:
    try:
        row = db.execute(
            text(
                """
                select
                  stat_date,
                  event_count,
                  manual_count,
                  connector_count,
                  avg_value,
                  min_value,
                  max_value
                from mart_poc_signal.signal_daily_summary
                where stat_date = :stat_date
                """
            ),
            {"stat_date": stat_date},
        ).mappings().first()
    except ProgrammingError as exc:
        db.rollback()
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message="mart model is unavailable, run dbt build first",
            http_status=503,
        ) from exc

    if not row:
        return {
            "stat_date": stat_date,
            "event_count": 0,
            "manual_count": 0,
            "connector_count": 0,
            "avg_value": 0.0,
            "min_value": 0.0,
            "max_value": 0.0,
        }

    return {
        "stat_date": row["stat_date"],
        "event_count": int(row["event_count"]),
        "manual_count": int(row["manual_count"]),
        "connector_count": int(row["connector_count"]),
        "avg_value": float(row["avg_value"] or 0),
        "min_value": float(row["min_value"] or 0),
        "max_value": float(row["max_value"] or 0),
    }


def get_connector_health(db: Session) -> dict:
    row = db.execute(
        text(
            """
            select
              last_run_at,
              last_status,
              success_count,
              failure_count
            from app.connector_health
            where id = 1
            """
        )
    ).mappings().first()

    if not row:
        return {
            "last_run_at": None,
            "last_status": "never",
            "success_count": 0,
            "failure_count": 0,
        }

    return {
        "last_run_at": row["last_run_at"],
        "last_status": row["last_status"],
        "success_count": int(row["success_count"]),
        "failure_count": int(row["failure_count"]),
    }
