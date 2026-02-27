from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


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
