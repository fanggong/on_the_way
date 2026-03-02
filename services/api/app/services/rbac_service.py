from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import AppError


def list_me_permissions(*, permissions: list[str]) -> dict:
    unique_permissions = sorted(set(permissions))
    return {
        "permissions": unique_permissions,
    }


def list_users_with_roles(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            select
              ua.user_id::text as user_id,
              ua.email,
              ua.status,
              ua.profile_completed,
              coalesce(
                array_agg(distinct ur.role_code)
                  filter (where ur.role_code is not null),
                '{}'::text[]
              ) as roles,
              ua.created_at,
              ua.updated_at
            from app.user_account ua
            left join app.rbac_user_role ur
              on ur.user_id = ua.user_id
            group by ua.user_id, ua.email, ua.status, ua.profile_completed, ua.created_at, ua.updated_at
            order by ua.created_at asc
            """
        )
    ).mappings().all()

    return [
        {
            "user_id": row["user_id"],
            "email": row["email"],
            "status": row["status"],
            "profile_completed": bool(row["profile_completed"]),
            "roles": list(row["roles"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def update_user_roles(db: Session, *, user_id: str, roles: list[str]) -> list[str]:
    exists = db.execute(
        text(
            """
            select exists(
              select 1 from app.user_account where user_id = cast(:user_id as uuid)
            )
            """
        ),
        {"user_id": user_id},
    ).scalar_one()

    if not exists:
        raise AppError(
            code="NOT_FOUND",
            message="target user not found",
            http_status=404,
        )

    db.execute(
        text(
            """
            delete from app.rbac_user_role
            where user_id = cast(:user_id as uuid)
            """
        ),
        {"user_id": user_id},
    )

    for role in roles:
        db.execute(
            text(
                """
                insert into app.rbac_user_role (user_id, role_code)
                values (cast(:user_id as uuid), :role_code)
                """
            ),
            {
                "user_id": user_id,
                "role_code": role,
            },
        )

    db.execute(
        text(
            """
            update app.user_account
            set updated_at = now()
            where user_id = cast(:user_id as uuid)
            """
        ),
        {"user_id": user_id},
    )

    db.commit()
    return roles
