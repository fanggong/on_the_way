from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import decode_token
from app.db.session import get_db


@dataclass
class CurrentUser:
    user_id: str
    email: str
    profile_completed: bool
    roles: list[str]
    permissions: list[str]


def _load_user_with_permissions(db: Session, *, user_id: str) -> CurrentUser:
    row = db.execute(
        text(
            """
            select
              ua.user_id::text as user_id,
              ua.email,
              ua.profile_completed,
              ua.status,
              coalesce(
                array_agg(distinct ur.role_code)
                  filter (where ur.role_code is not null),
                '{}'::text[]
              ) as roles,
              coalesce(
                array_agg(distinct rp.permission_code)
                  filter (where rp.permission_code is not null),
                '{}'::text[]
              ) as permissions
            from app.user_account ua
            left join app.rbac_user_role ur
              on ur.user_id = ua.user_id
            left join app.rbac_role_permission rp
              on rp.role_code = ur.role_code
            where ua.user_id = cast(:user_id as uuid)
            group by ua.user_id, ua.email, ua.profile_completed, ua.status
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not row:
        raise AppError(
            code="UNAUTHORIZED",
            message="user not found",
            http_status=401,
        )

    if row["status"] != "active":
        raise AppError(
            code="FORBIDDEN",
            message="user is disabled",
            http_status=403,
        )

    return CurrentUser(
        user_id=row["user_id"],
        email=row["email"],
        profile_completed=bool(row["profile_completed"]),
        roles=list(row["roles"]),
        permissions=list(row["permissions"]),
    )


def get_access_token(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization:
        raise AppError(
            code="UNAUTHORIZED",
            message="missing authorization header",
            http_status=401,
        )

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid authorization header",
            http_status=401,
        )

    return authorization[len(prefix) :].strip()


def get_current_user(
    token: str = Depends(get_access_token),
    db: Session = Depends(get_db),
) -> CurrentUser:
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid access token payload",
            http_status=401,
        )
    return _load_user_with_permissions(db, user_id=user_id)


def require_permission(permission_code: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission_code not in set(user.permissions):
            raise AppError(
                code="FORBIDDEN",
                message="permission denied",
                http_status=403,
            )
        return user

    return checker


def get_refresh_token_from_cookie(request: Request) -> str:
    token = request.cookies.get(settings.refresh_cookie_name, "").strip()
    if not token:
        raise AppError(
            code="UNAUTHORIZED",
            message="missing refresh token",
            http_status=401,
        )
    return token
