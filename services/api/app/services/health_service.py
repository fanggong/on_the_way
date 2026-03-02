from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError

DEFAULT_HEALTH_CONNECTOR_CONFIG = {
    "GARMIN_FETCH_WINDOW_DAYS": 3,
    "GARMIN_BACKFILL_DAYS": 10,
    "GARMIN_TIMEZONE": "Asia/Shanghai",
    "GARMIN_IS_CN": True,
}


def _parse_iso_date(value: str, *, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError(
            code="INVALID_ARGUMENT",
            message=f"{field_name} must be YYYY-MM-DD",
            http_status=400,
        ) from exc


def get_health_connector_config(db: Session) -> dict:
    row = db.execute(
        text(
            """
            select config_json
            from app.system_connector_option
            where system_code = 'health'
              and connector_code = 'garmin_connect'
            """
        )
    ).mappings().first()

    config = dict(DEFAULT_HEALTH_CONNECTOR_CONFIG)
    if row and isinstance(row["config_json"], dict):
        config.update(row["config_json"])

    return {
        "GARMIN_FETCH_WINDOW_DAYS": int(config["GARMIN_FETCH_WINDOW_DAYS"]),
        "GARMIN_BACKFILL_DAYS": int(config["GARMIN_BACKFILL_DAYS"]),
        "GARMIN_TIMEZONE": str(config["GARMIN_TIMEZONE"]),
        "GARMIN_IS_CN": bool(config["GARMIN_IS_CN"]),
    }


def update_health_connector_config(
    db: Session,
    *,
    GARMIN_FETCH_WINDOW_DAYS: int,
    GARMIN_BACKFILL_DAYS: int,
    GARMIN_TIMEZONE: str,
    GARMIN_IS_CN: bool,
) -> dict:
    config_json = {
        "GARMIN_FETCH_WINDOW_DAYS": GARMIN_FETCH_WINDOW_DAYS,
        "GARMIN_BACKFILL_DAYS": GARMIN_BACKFILL_DAYS,
        "GARMIN_TIMEZONE": GARMIN_TIMEZONE,
        "GARMIN_IS_CN": GARMIN_IS_CN,
    }

    updated = db.execute(
        text(
            """
            update app.system_connector_option
            set config_json = cast(:config_json as jsonb),
                updated_at = now()
            where system_code = 'health'
              and connector_code = 'garmin_connect'
            returning connector_code
            """
        ),
        {"config_json": json.dumps(config_json, ensure_ascii=True)},
    ).mappings().first()

    if not updated:
        db.rollback()
        raise AppError(
            code="NOT_FOUND",
            message="health garmin connector option not initialized",
            http_status=404,
        )

    db.commit()
    return config_json


def query_health_domain_metrics(
    db: Session,
    *,
    start_date: str,
    end_date: str,
    metric_name: str | None,
    account_ref: str | None,
    page: int,
    page_size: int,
) -> dict:
    start = _parse_iso_date(start_date, field_name="start_date")
    end = _parse_iso_date(end_date, field_name="end_date")
    if start > end:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="start_date must be <= end_date",
            http_status=400,
        )

    offset = (page - 1) * page_size

    params = {
        "start_date": start,
        "end_date": end,
        "metric_name": metric_name,
        "account_ref": account_ref,
        "limit": page_size,
        "offset": offset,
    }

    where_clause = """
        where metric_date between :start_date and :end_date
          and (cast(:metric_name as text) is null or metric_name = cast(:metric_name as text))
          and (cast(:account_ref as text) is null or account_ref = cast(:account_ref as text))
    """

    try:
        total = db.execute(
            text(
                f"""
                select count(*)
                from domain_health.health_metric_daily_fact
                {where_clause}
                """
            ),
            params,
        ).scalar_one()

        rows = db.execute(
            text(
                f"""
                select
                  domain_metric_row_id,
                  account_ref,
                  metric_date,
                  metric_type,
                  metric_name,
                  metric_value_num,
                  metric_value_text,
                  metric_unit,
                  quality_flag,
                  is_valid,
                  source_count,
                  first_occurred_at,
                  last_occurred_at,
                  latest_ingested_at
                from domain_health.health_metric_daily_fact
                {where_clause}
                order by metric_date desc, metric_name asc
                limit :limit offset :offset
                """
            ),
            params,
        ).mappings().all()
    except SQLAlchemyError as exc:
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message=f"domain model unavailable: {exc}",
            http_status=503,
        ) from exc

    return {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "items": [dict(row) for row in rows],
    }


def _query_mart_table(
    db: Session,
    *,
    table_name: str,
    start_date: str | None,
    end_date: str | None,
    account_ref: str | None,
    page: int,
    page_size: int,
) -> dict:
    start: date | None = None
    end: date | None = None
    if start_date:
        start = _parse_iso_date(start_date, field_name="start_date")
    if end_date:
        end = _parse_iso_date(end_date, field_name="end_date")
    if start and end and start > end:
        raise AppError(
            code="INVALID_ARGUMENT",
            message="start_date must be <= end_date",
            http_status=400,
        )

    offset = (page - 1) * page_size

    params: dict[str, Any] = {
        "start_date": start,
        "end_date": end,
        "account_ref": account_ref,
        "limit": page_size,
        "offset": offset,
    }

    where_clause = """
      where (cast(:start_date as date) is null or stat_date >= cast(:start_date as date))
        and (cast(:end_date as date) is null or stat_date <= cast(:end_date as date))
        and (cast(:account_ref as text) is null or account_ref = cast(:account_ref as text))
    """

    try:
        total = db.execute(
            text(
                f"""
                select count(*)
                from mart.{table_name}
                {where_clause}
                """
            ),
            params,
        ).scalar_one()

        rows = db.execute(
            text(
                f"""
                select *
                from mart.{table_name}
                {where_clause}
                order by stat_date desc
                limit :limit offset :offset
                """
            ),
            params,
        ).mappings().all()
    except SQLAlchemyError as exc:
        raise AppError(
            code="DEPENDENCY_UNAVAILABLE",
            message=f"mart model unavailable: {exc}",
            http_status=503,
        ) from exc

    return {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "items": [dict(row) for row in rows],
    }


def query_health_mart_overview(
    db: Session,
    *,
    start_date: str | None,
    end_date: str | None,
    account_ref: str | None,
    page: int,
    page_size: int,
) -> dict:
    return _query_mart_table(
        db,
        table_name="health_daily_overview",
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )


def query_health_mart_metric_summary(
    db: Session,
    *,
    start_date: str | None,
    end_date: str | None,
    account_ref: str | None,
    page: int,
    page_size: int,
) -> dict:
    return _query_mart_table(
        db,
        table_name="health_metric_daily_summary",
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )


def query_health_mart_activity_topics(
    db: Session,
    *,
    start_date: str | None,
    end_date: str | None,
    account_ref: str | None,
    page: int,
    page_size: int,
) -> dict:
    return _query_mart_table(
        db,
        table_name="health_activity_topic_daily",
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )
