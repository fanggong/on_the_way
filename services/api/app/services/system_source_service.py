from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import AppError

SYSTEM_LABELS: dict[str, str] = {
    "health": "健康",
    "time": "时间",
    "income": "收入",
    "finance": "财务",
    "ability": "能力",
    "relationship": "关系",
    "life": "生活",
    "security": "保障",
}


def _ensure_system_code(system_code: str) -> None:
    if system_code not in SYSTEM_LABELS:
        raise AppError(
            code="INVALID_ARGUMENT",
            message=f"unsupported system_code: {system_code}",
            http_status=400,
        )


def list_system_sources(db: Session) -> list[dict]:
    options_rows = db.execute(
        text(
            """
            select
              system_code,
              connector_code,
              display_name,
              enabled,
              updated_at
            from app.system_connector_option
            order by system_code, connector_code
            """
        )
    ).mappings().all()

    core_rows = db.execute(
        text(
            """
            select
              system_code,
              connector_code,
              auto_sync_enabled,
              auto_sync_interval_minutes,
              updated_at
            from app.system_core_source
            """
        )
    ).mappings().all()

    latest_job_rows = db.execute(
        text(
            """
            select distinct on (system_code)
              system_code,
              job_id::text as job_id,
              connector_code,
              job_type,
              status,
              backfill_start_at,
              backfill_end_at,
              triggered_at,
              finished_at,
              error_message
            from app.connector_sync_job
            order by system_code, triggered_at desc
            """
        )
    ).mappings().all()

    options_map: dict[str, list[dict]] = {code: [] for code in SYSTEM_LABELS}
    for row in options_rows:
        options_map.setdefault(row["system_code"], []).append(
            {
                "connector_code": row["connector_code"],
                "display_name": row["display_name"],
                "enabled": bool(row["enabled"]),
                "updated_at": row["updated_at"],
            }
        )

    core_map = {row["system_code"]: row for row in core_rows}
    latest_job_map = {row["system_code"]: row for row in latest_job_rows}

    result: list[dict] = []
    for system_code, system_name in SYSTEM_LABELS.items():
        core = core_map.get(system_code)
        latest_job = latest_job_map.get(system_code)
        result.append(
            {
                "system_code": system_code,
                "system_name": system_name,
                "available_connectors": options_map.get(system_code, []),
                "core_source": {
                    "connector_code": core["connector_code"] if core else None,
                    "auto_sync_enabled": bool(core["auto_sync_enabled"]) if core else False,
                    "auto_sync_interval_minutes": int(core["auto_sync_interval_minutes"]) if core else 60,
                    "updated_at": core["updated_at"] if core else None,
                },
                "latest_job": (
                    {
                        "job_id": latest_job["job_id"],
                        "connector_code": latest_job["connector_code"],
                        "job_type": latest_job["job_type"],
                        "status": latest_job["status"],
                        "backfill_start_at": latest_job["backfill_start_at"],
                        "backfill_end_at": latest_job["backfill_end_at"],
                        "triggered_at": latest_job["triggered_at"],
                        "finished_at": latest_job["finished_at"],
                        "error_message": latest_job["error_message"],
                    }
                    if latest_job
                    else None
                ),
            }
        )

    return result


def update_connector_enabled(
    db: Session,
    *,
    system_code: str,
    connector_code: str,
    enabled: bool,
    updated_by: str,
) -> None:
    _ensure_system_code(system_code)
    updated = db.execute(
        text(
            """
            update app.system_connector_option
            set enabled = :enabled,
                updated_at = now()
            where system_code = :system_code
              and connector_code = :connector_code
            """
        ),
        {
            "system_code": system_code,
            "connector_code": connector_code,
            "enabled": enabled,
        },
    )

    if updated.rowcount == 0:
        db.rollback()
        raise AppError(
            code="NOT_FOUND",
            message="connector option not found",
            http_status=404,
        )

    if not enabled:
        db.execute(
            text(
                """
                update app.system_core_source
                set connector_code = null,
                    auto_sync_enabled = false,
                    updated_by = cast(:updated_by as uuid),
                    updated_at = now()
                where system_code = :system_code
                  and connector_code = :connector_code
                """
            ),
            {
                "updated_by": updated_by,
                "system_code": system_code,
                "connector_code": connector_code,
            },
        )

    db.commit()


def update_core_source(
    db: Session,
    *,
    system_code: str,
    connector_code: str,
    updated_by: str,
) -> dict:
    _ensure_system_code(system_code)

    option = db.execute(
        text(
            """
            select enabled
            from app.system_connector_option
            where system_code = :system_code
              and connector_code = :connector_code
            """
        ),
        {
            "system_code": system_code,
            "connector_code": connector_code,
        },
    ).mappings().first()

    if not option:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="connector is not in system option list",
            http_status=400,
        )

    if not option["enabled"]:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="connector is disabled",
            http_status=400,
        )

    row = db.execute(
        text(
            """
            insert into app.system_core_source (
              system_code,
              connector_code,
              auto_sync_enabled,
              auto_sync_interval_minutes,
              updated_by,
              updated_at
            ) values (
              :system_code,
              :connector_code,
              false,
              60,
              cast(:updated_by as uuid),
              now()
            )
            on conflict (system_code) do update
            set connector_code = excluded.connector_code,
                updated_by = excluded.updated_by,
                updated_at = excluded.updated_at,
                auto_sync_enabled = case
                  when app.system_core_source.connector_code = excluded.connector_code
                    then app.system_core_source.auto_sync_enabled
                  else false
                end,
                auto_sync_interval_minutes = case
                  when app.system_core_source.connector_code = excluded.connector_code
                    then app.system_core_source.auto_sync_interval_minutes
                  else 60
                end
            returning
              system_code,
              connector_code,
              auto_sync_enabled,
              auto_sync_interval_minutes,
              updated_at
            """
        ),
        {
            "system_code": system_code,
            "connector_code": connector_code,
            "updated_by": updated_by,
        },
    ).mappings().one()
    db.commit()

    return {
        "system_code": row["system_code"],
        "connector_code": row["connector_code"],
        "auto_sync_enabled": bool(row["auto_sync_enabled"]),
        "auto_sync_interval_minutes": int(row["auto_sync_interval_minutes"]),
        "updated_at": row["updated_at"],
    }


def get_sync_policy(db: Session, *, system_code: str) -> dict:
    _ensure_system_code(system_code)
    row = db.execute(
        text(
            """
            select
              system_code,
              connector_code,
              auto_sync_enabled,
              auto_sync_interval_minutes,
              updated_at
            from app.system_core_source
            where system_code = :system_code
            """
        ),
        {"system_code": system_code},
    ).mappings().first()

    if not row:
        return {
            "system_code": system_code,
            "connector_code": None,
            "auto_sync_enabled": False,
            "auto_sync_interval_minutes": 60,
            "updated_at": None,
        }

    return {
        "system_code": row["system_code"],
        "connector_code": row["connector_code"],
        "auto_sync_enabled": bool(row["auto_sync_enabled"]),
        "auto_sync_interval_minutes": int(row["auto_sync_interval_minutes"]),
        "updated_at": row["updated_at"],
    }


def update_sync_policy(
    db: Session,
    *,
    system_code: str,
    auto_sync_enabled: bool,
    auto_sync_interval_minutes: int,
    updated_by: str,
) -> dict:
    _ensure_system_code(system_code)
    row = db.execute(
        text(
            """
            update app.system_core_source
            set auto_sync_enabled = :auto_sync_enabled,
                auto_sync_interval_minutes = :auto_sync_interval_minutes,
                updated_by = cast(:updated_by as uuid),
                updated_at = now()
            where system_code = :system_code
              and connector_code is not null
            returning
              system_code,
              connector_code,
              auto_sync_enabled,
              auto_sync_interval_minutes,
              updated_at
            """
        ),
        {
            "system_code": system_code,
            "auto_sync_enabled": auto_sync_enabled,
            "auto_sync_interval_minutes": auto_sync_interval_minutes,
            "updated_by": updated_by,
        },
    ).mappings().first()

    if not row:
        db.rollback()
        raise AppError(
            code="INVALID_ARGUMENT",
            message="core source is not configured",
            http_status=400,
        )

    db.commit()
    return {
        "system_code": row["system_code"],
        "connector_code": row["connector_code"],
        "auto_sync_enabled": bool(row["auto_sync_enabled"]),
        "auto_sync_interval_minutes": int(row["auto_sync_interval_minutes"]),
        "updated_at": row["updated_at"],
    }


def create_backfill_sync_job(
    db: Session,
    *,
    system_code: str,
    backfill_start_at: datetime,
    backfill_end_at: datetime,
    triggered_by: str,
) -> dict:
    _ensure_system_code(system_code)

    if backfill_end_at - backfill_start_at > timedelta(days=30):
        raise AppError(
            code="INVALID_ARGUMENT",
            message="backfill range exceeds 30 days",
            http_status=400,
        )

    core_source = db.execute(
        text(
            """
            select
              scs.connector_code
            from app.system_core_source scs
            join app.system_connector_option sco
              on sco.system_code = scs.system_code
             and sco.connector_code = scs.connector_code
            where scs.system_code = :system_code
              and scs.connector_code is not null
              and sco.enabled = true
            """
        ),
        {"system_code": system_code},
    ).mappings().first()

    if not core_source:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="core source is not configured or disabled",
            http_status=400,
        )

    has_running = db.execute(
        text(
            """
            select exists(
              select 1
              from app.connector_sync_job
              where system_code = :system_code
                and status = 'running'
            )
            """
        ),
        {"system_code": system_code},
    ).scalar_one()

    if has_running:
        raise AppError(
            code="CONFLICT",
            message="a sync job is already running",
            http_status=409,
        )

    row = db.execute(
        text(
            """
            insert into app.connector_sync_job (
              system_code,
              connector_code,
              job_type,
              backfill_start_at,
              backfill_end_at,
              status,
              triggered_by,
              triggered_at
            ) values (
              :system_code,
              :connector_code,
              'backfill_once',
              :backfill_start_at,
              :backfill_end_at,
              'queued',
              cast(:triggered_by as uuid),
              now()
            )
            returning
              job_id::text as job_id,
              system_code,
              connector_code,
              job_type,
              status,
              backfill_start_at,
              backfill_end_at,
              triggered_at
            """
        ),
        {
            "system_code": system_code,
            "connector_code": core_source["connector_code"],
            "backfill_start_at": backfill_start_at,
            "backfill_end_at": backfill_end_at,
            "triggered_by": triggered_by,
        },
    ).mappings().one()

    db.commit()
    return {
        "job_id": row["job_id"],
        "system_code": row["system_code"],
        "connector_code": row["connector_code"],
        "job_type": row["job_type"],
        "status": row["status"],
        "backfill_start_at": row["backfill_start_at"],
        "backfill_end_at": row["backfill_end_at"],
        "triggered_at": row["triggered_at"],
    }


def list_sync_jobs(db: Session, *, system_code: str, limit: int = 30) -> list[dict]:
    _ensure_system_code(system_code)
    rows = db.execute(
        text(
            """
            select
              job_id::text as job_id,
              system_code,
              connector_code,
              job_type,
              backfill_start_at,
              backfill_end_at,
              status,
              triggered_by::text as triggered_by,
              triggered_at,
              started_at,
              finished_at,
              error_message
            from app.connector_sync_job
            where system_code = :system_code
            order by triggered_at desc
            limit :limit
            """
        ),
        {
            "system_code": system_code,
            "limit": limit,
        },
    ).mappings().all()

    return [
        {
            "job_id": row["job_id"],
            "system_code": row["system_code"],
            "connector_code": row["connector_code"],
            "job_type": row["job_type"],
            "backfill_start_at": row["backfill_start_at"],
            "backfill_end_at": row["backfill_end_at"],
            "status": row["status"],
            "triggered_by": row["triggered_by"],
            "triggered_at": row["triggered_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "error_message": row["error_message"],
        }
        for row in rows
    ]
