from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

_ALLOWED_ROLES = {"super_admin", "admin", "analyst", "viewer"}


class UserRoleUpdateRequest(BaseModel):
    roles: list[str] = Field(min_length=1, max_length=8)

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, value: list[str]) -> list[str]:
        normalized = [role.strip() for role in value if role.strip()]
        if not normalized:
            raise ValueError("roles cannot be empty")
        invalid = [role for role in normalized if role not in _ALLOWED_ROLES]
        if invalid:
            raise ValueError(f"unsupported roles: {','.join(sorted(set(invalid)))}")
        dedup: list[str] = []
        seen: set[str] = set()
        for role in normalized:
            if role not in seen:
                dedup.append(role)
                seen.add(role)
        return dedup
