from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings
from app.core.errors import AppError

JWT_ALGORITHM = "HS256"
PASSWORD_HASHER = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return PASSWORD_HASHER.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _encode_token(payload: dict[str, Any], expires_delta: timedelta) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    token = jwt.encode(
        {
            **payload,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    return token, expires_at


def create_access_token(*, user_id: str, roles: list[str]) -> tuple[str, int]:
    token, _ = _encode_token(
        {
            "sub": user_id,
            "typ": "access",
            "roles": roles,
        },
        timedelta(minutes=settings.access_token_expires_minutes),
    )
    return token, settings.access_token_expires_minutes * 60


def create_refresh_token(*, user_id: str, session_id: str) -> tuple[str, datetime]:
    return _encode_token(
        {
            "sub": user_id,
            "sid": session_id,
            "typ": "refresh",
        },
        timedelta(days=settings.refresh_token_expires_days),
    )


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(
            code="UNAUTHORIZED",
            message="token expired",
            http_status=401,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid token",
            http_status=401,
        ) from exc

    if payload.get("typ") != expected_type:
        raise AppError(
            code="UNAUTHORIZED",
            message="invalid token type",
            http_status=401,
        )
    return payload
