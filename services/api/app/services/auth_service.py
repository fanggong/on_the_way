from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


def _load_roles_and_permissions(db: Session, *, user_id: str) -> tuple[list[str], list[str]]:
    row = db.execute(
        text(
            """
            select
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
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not row:
        return [], []
    return list(row["roles"]), list(row["permissions"])


def register_user(db: Session, *, email: str, password: str) -> dict:
    existing_user_count = db.execute(text("select count(*) from app.user_account")).scalar_one()
    role_code = "super_admin" if int(existing_user_count) == 0 else "viewer"

    try:
        inserted = db.execute(
            text(
                """
                insert into app.user_account (
                  email,
                  password_hash,
                  status,
                  profile_completed
                ) values (
                  :email,
                  :password_hash,
                  'active',
                  false
                )
                returning user_id::text as user_id, email
                """
            ),
            {
                "email": email,
                "password_hash": hash_password(password),
            },
        ).mappings().one()

        db.execute(
            text(
                """
                insert into app.rbac_user_role (user_id, role_code)
                values (cast(:user_id as uuid), :role_code)
                on conflict do nothing
                """
            ),
            {
                "user_id": inserted["user_id"],
                "role_code": role_code,
            },
        )

        default_display_name = email.split("@", 1)[0] or "user"
        db.execute(
            text(
                """
                insert into app.user_profile (
                  user_id,
                  display_name,
                  timezone
                ) values (
                  cast(:user_id as uuid),
                  :display_name,
                  'Asia/Shanghai'
                )
                on conflict (user_id) do nothing
                """
            ),
            {
                "user_id": inserted["user_id"],
                "display_name": default_display_name,
            },
        )

        db.commit()
        return {
            "user_id": inserted["user_id"],
            "email": inserted["email"],
            "roles": [role_code],
        }
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            code="EMAIL_ALREADY_EXISTS",
            message="email already registered",
            http_status=409,
        ) from exc


def login_user(db: Session, *, email: str, password: str) -> dict:
    row = db.execute(
        text(
            """
            select
              user_id::text as user_id,
              email,
              password_hash,
              status,
              profile_completed
            from app.user_account
            where email = :email
            """
        ),
        {"email": email},
    ).mappings().first()

    if not row or not verify_password(password, row["password_hash"]):
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid credentials",
            http_status=401,
        )

    if row["status"] != "active":
        raise AppError(
            code="FORBIDDEN",
            message="user is disabled",
            http_status=403,
        )

    roles, permissions = _load_roles_and_permissions(db, user_id=row["user_id"])
    if not roles:
        roles = ["viewer"]

    session_id = str(uuid4())
    refresh_token, refresh_expires_at = create_refresh_token(
        user_id=row["user_id"],
        session_id=session_id,
    )

    db.execute(
        text(
            """
            insert into app.user_session (
              session_id,
              user_id,
              refresh_token_hash,
              expires_at,
              revoked_at
            ) values (
              cast(:session_id as uuid),
              cast(:user_id as uuid),
              :refresh_token_hash,
              :expires_at,
              null
            )
            """
        ),
        {
            "session_id": session_id,
            "user_id": row["user_id"],
            "refresh_token_hash": hash_token(refresh_token),
            "expires_at": refresh_expires_at,
        },
    )
    db.commit()

    access_token, expires_in = create_access_token(
        user_id=row["user_id"],
        roles=roles,
    )

    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "profile_completed": bool(row["profile_completed"]),
        "user": {
            "user_id": row["user_id"],
            "email": row["email"],
            "roles": roles,
            "permissions": permissions,
        },
    }


def refresh_access_token(db: Session, *, refresh_token: str) -> dict:
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    session_id = payload.get("sid")

    if not isinstance(user_id, str) or not isinstance(session_id, str):
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid refresh token payload",
            http_status=401,
        )

    row = db.execute(
        text(
            """
            select
              ua.user_id::text as user_id,
              ua.email,
              ua.status,
              ua.profile_completed,
              us.refresh_token_hash,
              us.expires_at,
              us.revoked_at
            from app.user_account ua
            join app.user_session us
              on us.user_id = ua.user_id
            where ua.user_id = cast(:user_id as uuid)
              and us.session_id = cast(:session_id as uuid)
            """
        ),
        {
            "user_id": user_id,
            "session_id": session_id,
        },
    ).mappings().first()

    if not row:
        raise AppError(
            code="UNAUTHORIZED",
            message="refresh session not found",
            http_status=401,
        )

    if row["status"] != "active":
        raise AppError(
            code="FORBIDDEN",
            message="user is disabled",
            http_status=403,
        )

    if row["revoked_at"] is not None:
        raise AppError(
            code="UNAUTHORIZED",
            message="refresh token revoked",
            http_status=401,
        )

    if row["expires_at"] <= datetime.now(UTC):
        raise AppError(
            code="UNAUTHORIZED",
            message="refresh token expired",
            http_status=401,
        )

    if row["refresh_token_hash"] != hash_token(refresh_token):
        raise AppError(
            code="UNAUTHORIZED",
            message="refresh token mismatch",
            http_status=401,
        )

    roles, permissions = _load_roles_and_permissions(db, user_id=user_id)
    if not roles:
        roles = ["viewer"]

    access_token, expires_in = create_access_token(user_id=user_id, roles=roles)
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "profile_completed": bool(row["profile_completed"]),
        "user": {
            "user_id": row["user_id"],
            "email": row["email"],
            "roles": roles,
            "permissions": permissions,
        },
    }


def logout_refresh_token(db: Session, *, refresh_token: str) -> None:
    payload = decode_token(refresh_token, expected_type="refresh")
    session_id = payload.get("sid")
    if not isinstance(session_id, str):
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid refresh token payload",
            http_status=401,
        )

    db.execute(
        text(
            """
            update app.user_session
            set revoked_at = now()
            where session_id = cast(:session_id as uuid)
              and revoked_at is null
            """
        ),
        {"session_id": session_id},
    )
    db.commit()


def get_my_profile(db: Session, *, user_id: str, email: str, profile_completed: bool) -> dict:
    row = db.execute(
        text(
            """
            select
              user_id::text as user_id,
              display_name,
              timezone,
              gender,
              birth_date,
              height_cm,
              weight_kg
            from app.user_profile
            where user_id = cast(:user_id as uuid)
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not row:
        return {
            "user_id": user_id,
            "display_name": email.split("@", 1)[0] or "user",
            "timezone": "Asia/Shanghai",
            "gender": None,
            "birth_date": None,
            "height_cm": None,
            "weight_kg": None,
            "profile_completed": profile_completed,
        }

    return {
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "timezone": row["timezone"],
        "gender": row["gender"],
        "birth_date": row["birth_date"],
        "height_cm": float(row["height_cm"]) if row["height_cm"] is not None else None,
        "weight_kg": float(row["weight_kg"]) if row["weight_kg"] is not None else None,
        "profile_completed": profile_completed,
    }


def upsert_my_profile(
    db: Session,
    *,
    user_id: str,
    display_name: str,
    timezone: str,
    gender: str | None,
    birth_date,
    height_cm: float | None,
    weight_kg: float | None,
) -> dict:
    row = db.execute(
        text(
            """
            insert into app.user_profile (
              user_id,
              display_name,
              timezone,
              gender,
              birth_date,
              height_cm,
              weight_kg,
              updated_at
            ) values (
              cast(:user_id as uuid),
              :display_name,
              :timezone,
              :gender,
              :birth_date,
              :height_cm,
              :weight_kg,
              now()
            )
            on conflict (user_id) do update
            set display_name = excluded.display_name,
                timezone = excluded.timezone,
                gender = excluded.gender,
                birth_date = excluded.birth_date,
                height_cm = excluded.height_cm,
                weight_kg = excluded.weight_kg,
                updated_at = now()
            returning
              user_id::text as user_id,
              display_name,
              timezone,
              gender,
              birth_date,
              height_cm,
              weight_kg
            """
        ),
        {
            "user_id": user_id,
            "display_name": display_name,
            "timezone": timezone,
            "gender": gender,
            "birth_date": birth_date,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
        },
    ).mappings().one()

    db.execute(
        text(
            """
            update app.user_account
            set profile_completed = true,
                updated_at = now()
            where user_id = cast(:user_id as uuid)
            """
        ),
        {"user_id": user_id},
    )
    db.commit()

    return {
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "timezone": row["timezone"],
        "gender": row["gender"],
        "birth_date": row["birth_date"],
        "height_cm": float(row["height_cm"]) if row["height_cm"] is not None else None,
        "weight_kg": float(row["weight_kg"]) if row["weight_kg"] is not None else None,
        "profile_completed": True,
    }
