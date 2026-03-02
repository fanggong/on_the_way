from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.auth import (
    CurrentUser,
    get_current_user,
    get_refresh_token_from_cookie,
    require_permission,
)
from app.core.config import settings
from app.core.errors import AppError
from app.core.rate_limit import build_rate_limit_guard
from app.db.session import get_db
from app.schemas.annotation import AnnotationCreateRequest
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.health_query import HealthConnectorConfigUpdateRequest
from app.schemas.ingest import HealthConnectorIngestRequest, IngestResponse
from app.schemas.profile import ProfileUpsertRequest
from app.schemas.rbac import UserRoleUpdateRequest
from app.schemas.system_source import (
    ConnectorEnableRequest,
    CoreSourceUpdateRequest,
    SyncJobCreateRequest,
    SyncPolicyUpdateRequest,
)
from app.services.annotation_service import create_annotation
from app.services.auth_service import (
    get_my_profile,
    login_user,
    logout_refresh_token,
    refresh_access_token,
    register_user,
    upsert_my_profile,
)
from app.services.health_service import (
    get_health_connector_config,
    query_health_domain_metrics,
    query_health_mart_activity_topics,
    query_health_mart_metric_summary,
    query_health_mart_overview,
    update_health_connector_config,
)
from app.services.ingest_service import ingest_signal, register_ingest_error
from app.services.query_service import get_connector_health
from app.services.rbac_service import list_me_permissions, list_users_with_roles, update_user_roles
from app.services.system_source_service import (
    create_backfill_sync_job,
    get_sync_policy,
    list_sync_jobs,
    list_system_sources,
    update_connector_enabled,
    update_core_source,
    update_sync_policy,
)

router = APIRouter(prefix="/v1", tags=["v1"])
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
auth_rate_guard = build_rate_limit_guard(
    action="auth",
    limit=settings.auth_rate_limit_per_minute,
    window_seconds=60,
)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expires_days * 24 * 3600,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/",
    )


@router.get("/health/live")
def health_live() -> dict:
    return {
        "status": "ok",
        "service": "api-service",
        "time": datetime.now(SHANGHAI_TZ).isoformat(),
    }


@router.get("/health/connector")
def health_connector(db: Session = Depends(get_db)) -> dict:
    health = get_connector_health(db)
    return {"status": "ok", **health}


@router.post("/ingest/connector-health", response_model=IngestResponse)
def ingest_connector_health(
    body: HealthConnectorIngestRequest,
    db: Session = Depends(get_db),
) -> dict:
    request_id = str(uuid4())
    try:
        result = ingest_signal(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            occurred_at=body.occurred_at,
            payload=body.payload.model_dump(mode="json"),
        )
        return {
            "status": "ok",
            "raw_id": result.raw_id,
            "ingested_at": result.ingested_at,
            "idempotent": result.idempotent,
        }
    except AppError as exc:
        register_ingest_error(
            db,
            request_id=request_id,
            source_id=body.source_id,
            external_id=body.external_id,
            code=exc.code,
            message=exc.message,
        )
        exc.request_id = request_id
        raise


@router.post("/annotation")
def post_annotation(
    body: AnnotationCreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    annotation_id, created_at = create_annotation(
        db,
        target_type=body.target_type,
        target_id=body.target_id,
        label=body.label,
        value=body.value,
    )
    return {
        "status": "ok",
        "annotation_id": annotation_id,
        "created_at": created_at,
    }


@router.post("/auth/register", dependencies=[Depends(auth_rate_guard)])
def auth_register(body: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    user = register_user(db, email=body.email, password=body.password)
    return {
        "status": "ok",
        "data": {
            "user_id": user["user_id"],
            "email": user["email"],
        },
    }


@router.post("/auth/login", dependencies=[Depends(auth_rate_guard)])
def auth_login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    login_result = login_user(db, email=body.email, password=body.password)
    _set_refresh_cookie(response, login_result["refresh_token"])

    return {
        "status": "ok",
        "data": {
            "access_token": login_result["access_token"],
            "expires_in": login_result["expires_in"],
            "profile_completed": login_result["profile_completed"],
            "user": {
                "user_id": login_result["user"]["user_id"],
                "email": login_result["user"]["email"],
                "roles": login_result["user"]["roles"],
            },
        },
    }


@router.post("/auth/refresh")
def auth_refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    refresh_token = get_refresh_token_from_cookie(request)
    refreshed = refresh_access_token(db, refresh_token=refresh_token)
    return {
        "status": "ok",
        "data": {
            "access_token": refreshed["access_token"],
            "expires_in": refreshed["expires_in"],
            "profile_completed": refreshed["profile_completed"],
            "user": {
                "user_id": refreshed["user"]["user_id"],
                "email": refreshed["user"]["email"],
                "roles": refreshed["user"]["roles"],
            },
        },
    }


@router.post("/auth/logout")
def auth_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    refresh_token = request.cookies.get(settings.refresh_cookie_name, "").strip()
    if refresh_token:
        try:
            logout_refresh_token(db, refresh_token=refresh_token)
        except AppError:
            pass
    _clear_refresh_cookie(response)
    return {"status": "ok", "data": {"logged_out": True}}


@router.get("/auth/me")
def auth_me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {
        "status": "ok",
        "data": {
            "user_id": user.user_id,
            "email": user.email,
            "roles": user.roles,
            "permissions": sorted(set(user.permissions)),
            "profile_completed": user.profile_completed,
        },
    }


@router.get("/profile/me")
def profile_me(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile = get_my_profile(
        db,
        user_id=user.user_id,
        email=user.email,
        profile_completed=user.profile_completed,
    )
    return {
        "status": "ok",
        "data": profile,
    }


@router.put("/profile/me")
def profile_update(
    body: ProfileUpsertRequest,
    user: CurrentUser = Depends(require_permission("profile.write")),
    db: Session = Depends(get_db),
) -> dict:
    profile = upsert_my_profile(
        db,
        user_id=user.user_id,
        display_name=body.display_name,
        timezone=body.timezone,
        gender=body.gender,
        birth_date=body.birth_date,
        height_cm=body.height_cm,
        weight_kg=body.weight_kg,
    )
    return {
        "status": "ok",
        "data": profile,
    }


@router.get("/rbac/me-permissions")
def rbac_me_permissions(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {
        "status": "ok",
        "data": list_me_permissions(permissions=user.permissions),
    }


@router.get("/rbac/users")
def rbac_list_users(
    _: CurrentUser = Depends(require_permission("rbac.user_role.write")),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "status": "ok",
        "data": {
            "items": list_users_with_roles(db),
        },
    }


@router.put("/rbac/users/{user_id}/roles")
def rbac_update_user_roles(
    user_id: str,
    body: UserRoleUpdateRequest,
    _: CurrentUser = Depends(require_permission("rbac.user_role.write")),
    db: Session = Depends(get_db),
) -> dict:
    roles = update_user_roles(db, user_id=user_id, roles=body.roles)
    return {
        "status": "ok",
        "data": {
            "user_id": user_id,
            "roles": roles,
        },
    }


@router.get("/system-sources")
def get_system_sources(
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "status": "ok",
        "data": {
            "items": list_system_sources(db),
        },
    }


@router.put("/system-sources/{system_code}/core-source")
def put_system_core_source(
    system_code: str,
    body: CoreSourceUpdateRequest,
    user: CurrentUser = Depends(require_permission("system_source.write")),
    db: Session = Depends(get_db),
) -> dict:
    data = update_core_source(
        db,
        system_code=system_code,
        connector_code=body.connector_code,
        updated_by=user.user_id,
    )
    return {"status": "ok", "data": data}


@router.put("/system-sources/{system_code}/connectors/{connector_code}")
def put_system_connector_enabled(
    system_code: str,
    connector_code: str,
    body: ConnectorEnableRequest,
    user: CurrentUser = Depends(require_permission("system_source.write")),
    db: Session = Depends(get_db),
) -> dict:
    update_connector_enabled(
        db,
        system_code=system_code,
        connector_code=connector_code,
        enabled=body.enabled,
        updated_by=user.user_id,
    )
    return {
        "status": "ok",
        "data": {
            "system_code": system_code,
            "connector_code": connector_code,
            "enabled": body.enabled,
        },
    }


@router.get("/system-sources/{system_code}/sync-policy")
def get_system_sync_policy(
    system_code: str,
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = get_sync_policy(db, system_code=system_code)
    return {"status": "ok", "data": data}


@router.put("/system-sources/{system_code}/sync-policy")
def put_system_sync_policy(
    system_code: str,
    body: SyncPolicyUpdateRequest,
    user: CurrentUser = Depends(require_permission("system_source.write")),
    db: Session = Depends(get_db),
) -> dict:
    data = update_sync_policy(
        db,
        system_code=system_code,
        auto_sync_enabled=body.auto_sync_enabled,
        auto_sync_interval_minutes=body.auto_sync_interval_minutes,
        updated_by=user.user_id,
    )
    return {"status": "ok", "data": data}


@router.post("/system-sources/{system_code}/sync-jobs")
def post_system_sync_job(
    system_code: str,
    body: SyncJobCreateRequest,
    user: CurrentUser = Depends(require_permission("system_source.write")),
    db: Session = Depends(get_db),
) -> dict:
    data = create_backfill_sync_job(
        db,
        system_code=system_code,
        backfill_start_at=body.backfill_start_at,
        backfill_end_at=body.backfill_end_at,
        triggered_by=user.user_id,
    )
    return {"status": "ok", "data": data}


@router.get("/system-sources/{system_code}/sync-jobs")
def get_system_sync_jobs(
    system_code: str,
    limit: int = Query(default=30, ge=1, le=200),
    _: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "status": "ok",
        "data": {
            "items": list_sync_jobs(db, system_code=system_code, limit=limit),
        },
    }


@router.get("/health/connectors/config")
def get_health_connectors_config(
    _: CurrentUser = Depends(require_permission("health.mart.read")),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "status": "ok",
        "data": get_health_connector_config(db),
    }


@router.put("/health/connectors/config")
def put_health_connectors_config(
    body: HealthConnectorConfigUpdateRequest,
    _: CurrentUser = Depends(require_permission("health.connector.write")),
    db: Session = Depends(get_db),
) -> dict:
    data = update_health_connector_config(
        db,
        GARMIN_FETCH_WINDOW_DAYS=body.GARMIN_FETCH_WINDOW_DAYS,
        GARMIN_BACKFILL_DAYS=body.GARMIN_BACKFILL_DAYS,
        GARMIN_TIMEZONE=body.GARMIN_TIMEZONE,
        GARMIN_IS_CN=body.GARMIN_IS_CN,
    )
    return {
        "status": "ok",
        "data": data,
    }


@router.get("/health/domain/metrics")
def get_health_domain_metrics(
    start_date: str,
    end_date: str,
    metric_name: str | None = None,
    account_ref: str | None = None,
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=20, ge=1, le=200),
    _: CurrentUser = Depends(require_permission("health.domain.read")),
    db: Session = Depends(get_db),
) -> dict:
    data = query_health_domain_metrics(
        db,
        start_date=start_date,
        end_date=end_date,
        metric_name=metric_name,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )
    return {
        "status": "ok",
        "data": data,
    }


@router.get("/health/mart/overview")
def get_health_mart_overview(
    start_date: str | None = None,
    end_date: str | None = None,
    account_ref: str | None = None,
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=20, ge=1, le=200),
    _: CurrentUser = Depends(require_permission("health.mart.read")),
    db: Session = Depends(get_db),
) -> dict:
    data = query_health_mart_overview(
        db,
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )
    return {"status": "ok", "data": data}


@router.get("/health/mart/metric-summary")
def get_health_mart_metric_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    account_ref: str | None = None,
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=20, ge=1, le=200),
    _: CurrentUser = Depends(require_permission("health.mart.read")),
    db: Session = Depends(get_db),
) -> dict:
    data = query_health_mart_metric_summary(
        db,
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )
    return {"status": "ok", "data": data}


@router.get("/health/mart/activity-topics")
def get_health_mart_activity_topics(
    start_date: str | None = None,
    end_date: str | None = None,
    account_ref: str | None = None,
    page: int = Query(default=1, ge=1, le=100000),
    page_size: int = Query(default=20, ge=1, le=200),
    _: CurrentUser = Depends(require_permission("health.mart.read")),
    db: Session = Depends(get_db),
) -> dict:
    data = query_health_mart_activity_topics(
        db,
        start_date=start_date,
        end_date=end_date,
        account_ref=account_ref,
        page=page,
        page_size=page_size,
    )
    return {"status": "ok", "data": data}
