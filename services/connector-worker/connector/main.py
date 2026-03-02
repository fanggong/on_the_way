from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, time as time_value, timedelta
from hashlib import sha256
from typing import Any, Literal
from zoneinfo import ZoneInfo

import httpx
import psycopg
from psycopg.rows import dict_row

from connector.config import DEFAULT_METRICS, settings

try:
    from garminconnect import Garmin
except Exception as exc:  # pragma: no cover - handled at runtime
    Garmin = None
    GARMIN_IMPORT_ERROR = str(exc)
else:  # pragma: no cover - import branch depends on runtime image
    GARMIN_IMPORT_ERROR = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [connector] %(message)s",
)
logger = logging.getLogger(__name__)

MethodMode = Literal["date", "range", "none"]


@dataclass(frozen=True)
class MetricMethod:
    name: str
    mode: MethodMode


@dataclass
class CycleStats:
    ingested: int = 0
    no_data: int = 0
    not_supported: int = 0
    errors: int = 0


@dataclass(frozen=True)
class SyncPolicyContext:
    connector_code: str
    auto_sync_enabled: bool
    auto_sync_interval_minutes: int
    config_json: dict[str, Any]


@dataclass(frozen=True)
class SyncJob:
    job_id: str
    connector_code: str
    job_type: str
    backfill_start_at: datetime | None
    backfill_end_at: datetime | None


METRIC_METHODS: dict[str, tuple[MetricMethod, ...]] = {
    "user_summary": (MetricMethod("get_user_summary", "date"),),
    "sleep": (MetricMethod("get_sleep_data", "date"),),
    "heart_rate": (
        MetricMethod("get_heart_rates", "date"),
        MetricMethod("get_heart_rate", "date"),
    ),
    "resting_heart_rate": (
        MetricMethod("get_rhr_day", "date"),
        MetricMethod("get_resting_heart_rate", "date"),
    ),
    "stress": (MetricMethod("get_stress_data", "date"),),
    "body_battery": (MetricMethod("get_body_battery", "range"),),
    "respiration": (MetricMethod("get_respiration_data", "date"),),
    "spo2": (MetricMethod("get_spo2_data", "date"),),
    "hrv": (
        MetricMethod("get_hrv_data", "date"),
        MetricMethod("get_hrv_summary", "date"),
    ),
    "intensity_minutes": (
        MetricMethod("get_intensity_minutes_data", "date"),
        MetricMethod("get_intensity_minutes", "date"),
    ),
    "weight": (
        MetricMethod("get_weigh_ins", "date"),
        MetricMethod("get_body_composition", "date"),
    ),
    "body_composition": (
        MetricMethod("get_body_composition", "date"),
        MetricMethod("get_body_composition_by_date", "date"),
    ),
    "hydration": (
        MetricMethod("get_hydration_data", "date"),
        MetricMethod("get_hydration", "date"),
    ),
    "blood_pressure": (
        MetricMethod("get_blood_pressure", "date"),
        MetricMethod("get_blood_pressure_data", "date"),
    ),
    "menstrual": (
        MetricMethod("get_menstrual_data", "date"),
        MetricMethod("get_cycle_tracking_data", "date"),
    ),
    "pregnancy": (MetricMethod("get_pregnancy_data", "date"),),
    "activities": (
        MetricMethod("get_activities_by_date", "date"),
        MetricMethod("get_activities", "date"),
    ),
    "training_status": (MetricMethod("get_training_status", "date"),),
    "training_readiness": (MetricMethod("get_training_readiness", "date"),),
    "recovery_time": (
        MetricMethod("get_recovery_time_data", "date"),
        MetricMethod("get_recovery_time", "date"),
    ),
    "max_metrics_vo2": (
        MetricMethod("get_max_metrics", "date"),
        MetricMethod("get_vo2_max_data", "date"),
    ),
    "race_prediction": (
        MetricMethod("get_race_predictions", "none"),
        MetricMethod("get_race_prediction", "date"),
    ),
    "hill_score": (MetricMethod("get_hill_score", "date"),),
    "endurance_score": (MetricMethod("get_endurance_score", "date"),),
    "lactate_threshold": (MetricMethod("get_lactate_threshold", "date"),),
    "workouts": (MetricMethod("get_workouts", "none"),),
    "training_plans": (MetricMethod("get_training_plans", "none"),),
    "devices": (MetricMethod("get_devices", "none"),),
    "gear": (MetricMethod("get_gear", "none"),),
    "goals": (MetricMethod("get_goals", "none"),),
    "badges": (MetricMethod("get_badges", "none"),),
    "challenges": (MetricMethod("get_challenges", "none"),),
}

SNAPSHOT_METRICS = {
    "workouts",
    "training_plans",
    "devices",
    "gear",
    "goals",
    "badges",
    "challenges",
}


def update_connector_health(status: str) -> None:
    with psycopg.connect(
        settings.db_url,
        options="-c timezone=Asia/Shanghai",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into app.connector_health (
                  id, last_run_at, last_status, success_count, failure_count, updated_at
                ) values (
                  1, now(), %s,
                  case when %s = 'ok' then 1 else 0 end,
                  case when %s = 'error' then 1 else 0 end,
                  now()
                )
                on conflict (id) do update
                set
                  last_run_at = excluded.last_run_at,
                  last_status = excluded.last_status,
                  success_count = app.connector_health.success_count +
                    case when excluded.last_status = 'ok' then 1 else 0 end,
                  failure_count = app.connector_health.failure_count +
                    case when excluded.last_status = 'error' then 1 else 0 end,
                  updated_at = excluded.updated_at;
                """,
                (status, status, status),
            )
        conn.commit()


def _hash_payload(payload: dict[str, Any]) -> str:
    payload_bytes = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(payload_bytes).hexdigest()


def _build_account_ref(email: str) -> str:
    return sha256(email.strip().lower().encode("utf-8")).hexdigest()[:12]


def _resolve_metric_list() -> tuple[str, ...]:
    allowed = set(DEFAULT_METRICS)
    valid = tuple(metric for metric in settings.garmin_metrics if metric in allowed)
    invalid = [metric for metric in settings.garmin_metrics if metric not in allowed]

    if invalid:
        logger.warning("ignore unsupported metrics from GARMIN_METRICS=%s", ",".join(invalid))

    if valid:
        return valid

    logger.warning("no valid metrics provided, fallback to full metric list")
    return tuple(DEFAULT_METRICS)


def _resolve_metric_dates(now_local_date: date, *, days: int) -> list[date]:
    days = max(days, 1)
    start_date = now_local_date - timedelta(days=days - 1)
    return [start_date + timedelta(days=index) for index in range(days)]


def _resolve_target_dates(metric_type: str, window_dates: list[date]) -> list[date]:
    if metric_type in SNAPSHOT_METRICS:
        return [window_dates[-1]]
    return window_dates


def _build_occurred_at(metric_date: date, timezone: ZoneInfo) -> datetime:
    return datetime.combine(metric_date, time_value.min, tzinfo=timezone)


def _normalize_data(raw_data: Any) -> dict[str, Any]:
    if isinstance(raw_data, dict):
        return raw_data
    return {"value": raw_data}


def _build_ingest_request(
    *,
    metric_type: str,
    metric_date: date,
    timezone: ZoneInfo,
    timezone_name: str,
    account_ref: str,
    api_method: str | None,
    raw_data: Any,
) -> dict[str, Any]:
    fetched_at = datetime.now(timezone)
    payload = {
        "connector": "garmin_connect",
        "connector_version": settings.connector_version,
        "account_ref": account_ref,
        "metric_type": metric_type,
        "metric_date": metric_date.isoformat(),
        "timezone": timezone_name,
        "fetched_at": fetched_at.isoformat(),
        "api_method": api_method,
        "data": _normalize_data(raw_data),
    }

    payload_digest = _hash_payload(payload)[:16]
    external_id = (
        f"garmin::{account_ref}::{metric_type}::{metric_date.isoformat()}::{payload_digest}"
    )
    occurred_at = _build_occurred_at(metric_date, timezone)

    return {
        "source_id": settings.source_id,
        "external_id": external_id,
        "occurred_at": occurred_at.isoformat(),
        "payload": payload,
    }


def _invoke_method(method: Any, *, mode: MethodMode, metric_date: date) -> tuple[str, Any, str | None]:
    day_value = metric_date.isoformat()

    if mode == "date":
        attempts = [
            ((day_value,), {}),
            ((metric_date,), {}),
            ((), {"cdate": day_value}),
            ((), {"date": day_value}),
        ]
    elif mode == "range":
        attempts = [
            ((day_value, day_value), {}),
            ((metric_date, metric_date), {}),
            ((), {"startdate": day_value, "enddate": day_value}),
            ((), {"start": day_value, "end": day_value}),
        ]
    else:
        attempts = [
            ((), {}),
        ]

    signature_error: str | None = None
    for args, kwargs in attempts:
        try:
            return "ok", method(*args, **kwargs), None
        except TypeError as exc:
            signature_error = str(exc)
            continue
        except Exception as exc:  # pragma: no cover - depends on Garmin account/runtime
            return "error", None, str(exc)

    return "not_supported", None, signature_error or "no compatible method signature"


def _is_no_data(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, bytes, list, tuple, set, dict)):
        return len(value) == 0
    return False


def _has_metric_signal(metric_type: str, data: Any) -> bool:
    if not isinstance(data, dict):
        return True

    if metric_type == "heart_rate":
        heart_rate_values = data.get("heartRateValues")
        if isinstance(heart_rate_values, (list, dict)) and len(heart_rate_values) > 0:
            return True
        for key in (
            "restingHeartRate",
            "maxHeartRate",
            "minHeartRate",
            "lastSevenDaysAvgRestingHeartRate",
        ):
            value = data.get(key)
            if value not in (None, "", 0):
                return True
        return False

    if metric_type == "resting_heart_rate":
        metrics_map = (data.get("allMetrics") or {}).get("metricsMap")
        if isinstance(metrics_map, dict) and len(metrics_map) > 0:
            return True
        grouped_metrics = data.get("groupedMetrics")
        if isinstance(grouped_metrics, dict) and len(grouped_metrics) > 0:
            return True
        return False

    return True


def _fetch_metric(
    garmin_client: Any,
    *,
    metric_type: str,
    metric_date: date,
) -> tuple[str, Any, str | None, str | None]:
    methods = METRIC_METHODS.get(metric_type, ())
    if not methods:
        return "not_supported", None, None, "metric mapping missing"

    has_callable_method = False
    errors: list[str] = []
    for metric_method in methods:
        method = getattr(garmin_client, metric_method.name, None)
        if not callable(method):
            continue

        has_callable_method = True
        status, data, err = _invoke_method(
            method,
            mode=metric_method.mode,
            metric_date=metric_date,
        )
        if status == "ok":
            if _is_no_data(data) or not _has_metric_signal(metric_type, data):
                return "no_data", None, metric_method.name, None
            return "ok", data, metric_method.name, None

        if status == "not_supported":
            continue

        errors.append(f"{metric_method.name}: {err}")

    if not has_callable_method:
        return "not_supported", None, None, "no callable SDK method found"

    if errors:
        return "error", None, None, "; ".join(errors[-3:])

    return "not_supported", None, None, "all mapped methods unsupported"


def _try_resume_mfa(garmin_client: Any, mfa_code: str) -> bool:
    candidates = (
        "resume_login",
        "submit_mfa_code",
        "validate_mfa",
    )

    for method_name in candidates:
        method = getattr(garmin_client, method_name, None)
        if not callable(method):
            continue

        attempts = [
            ((mfa_code,), {}),
            ((), {"code": mfa_code}),
            ((), {"mfa_code": mfa_code}),
        ]
        for args, kwargs in attempts:
            try:
                method(*args, **kwargs)
                return True
            except TypeError:
                continue
            except Exception as exc:  # pragma: no cover - runtime behavior
                logger.warning("MFA resume failed method=%s err=%s", method_name, exc)
                return False

    return False


def _build_garmin_client(*, runtime_is_cn: bool) -> Any:
    if Garmin is None:
        raise RuntimeError(f"garminconnect import failed: {GARMIN_IMPORT_ERROR}")

    configured_is_cn = runtime_is_cn
    fallback_is_cn = not configured_is_cn
    constructors = [
        lambda: Garmin(
            settings.garmin_email,
            settings.garmin_password,
            is_cn=configured_is_cn,
        ),
        lambda: Garmin(email=settings.garmin_email, password=settings.garmin_password),
        lambda: Garmin(
            settings.garmin_email,
            settings.garmin_password,
            is_cn=fallback_is_cn,
        ),
        lambda: Garmin(
            email=settings.garmin_email,
            password=settings.garmin_password,
            is_cn=configured_is_cn,
            tokenstore_basepath=settings.garmin_token_dir,
        ),
    ]

    last_error: Exception | None = None
    for constructor in constructors:
        try:
            return constructor()
        except TypeError as exc:
            last_error = exc
            continue

    raise RuntimeError(f"unable to construct Garmin client: {last_error}")


def _login_garmin(garmin_client: Any) -> None:
    login_method = getattr(garmin_client, "login", None)
    if not callable(login_method):
        raise RuntimeError("Garmin client has no login method")

    attempts = [
        ((), {"tokenstore_basepath": settings.garmin_token_dir}),
        ((), {"tokenstore": settings.garmin_token_dir}),
        ((), {"token_store": settings.garmin_token_dir}),
        ((settings.garmin_token_dir,), {}),
        ((), {}),
    ]

    last_error: Exception | None = None
    for args, kwargs in attempts:
        try:
            login_method(*args, **kwargs)
            return
        except TypeError:
            continue
        except Exception as exc:  # pragma: no cover - runtime behavior
            if settings.garmin_mfa_code and _try_resume_mfa(
                garmin_client,
                settings.garmin_mfa_code,
            ):
                return
            last_error = exc
            continue

    if last_error is not None:
        raise RuntimeError(f"garmin login failed: {last_error}") from last_error
    raise RuntimeError("garmin login signature is incompatible with current client")


def _send_ingest(
    http_client: httpx.Client,
    *,
    ingest_body: dict[str, Any],
    metric_type: str,
    metric_date: date,
) -> bool:
    url = f"{settings.api_base_url.rstrip('/')}{settings.ingest_path}"

    for attempt in range(1, settings.retry_attempts + 1):
        try:
            response = http_client.post(url, json=ingest_body)
            if response.status_code == 200:
                body = response.json()
                logger.info(
                    "ingested metric_type=%s metric_date=%s external_id=%s raw_id=%s idempotent=%s",
                    metric_type,
                    metric_date.isoformat(),
                    ingest_body["external_id"],
                    body.get("raw_id"),
                    body.get("idempotent"),
                )
                return True

            logger.warning(
                "ingest failed metric_type=%s metric_date=%s status=%s attempt=%s body=%s",
                metric_type,
                metric_date.isoformat(),
                response.status_code,
                attempt,
                response.text,
            )
        except Exception as exc:  # pragma: no cover - network/runtime behavior
            logger.warning(
                "ingest exception metric_type=%s metric_date=%s attempt=%s err=%s",
                metric_type,
                metric_date.isoformat(),
                attempt,
                exc,
            )

        if attempt < settings.retry_attempts:
            time.sleep(2 ** (attempt - 1))

    return False


def _run_cycle(
    http_client: httpx.Client,
    *,
    timezone: ZoneInfo,
    timezone_name: str,
    runtime_is_cn: bool,
    metrics: tuple[str, ...],
    metric_dates: list[date],
) -> CycleStats:
    stats = CycleStats()

    if not settings.garmin_email or not settings.garmin_password:
        logger.error("GARMIN_EMAIL/GARMIN_PASSWORD not configured; skip cycle")
        stats.errors += 1
        return stats

    try:
        garmin_client = _build_garmin_client(runtime_is_cn=runtime_is_cn)
        _login_garmin(garmin_client)
    except Exception as exc:
        logger.error("garmin auth failed: %s", exc)
        stats.errors += 1
        return stats

    account_ref = _build_account_ref(settings.garmin_email)

    for metric_type in metrics:
        target_dates = _resolve_target_dates(metric_type, metric_dates)
        for metric_date in target_dates:
            status, data, api_method, err = _fetch_metric(
                garmin_client,
                metric_type=metric_type,
                metric_date=metric_date,
            )

            if status == "ok":
                ingest_body = _build_ingest_request(
                    metric_type=metric_type,
                    metric_date=metric_date,
                    timezone=timezone,
                    timezone_name=timezone_name,
                    account_ref=account_ref,
                    api_method=api_method,
                    raw_data=data,
                )
                if _send_ingest(
                    http_client,
                    ingest_body=ingest_body,
                    metric_type=metric_type,
                    metric_date=metric_date,
                ):
                    stats.ingested += 1
                else:
                    stats.errors += 1
                continue

            if status == "no_data":
                stats.no_data += 1
                logger.info(
                    "no_data metric_type=%s metric_date=%s",
                    metric_type,
                    metric_date.isoformat(),
                )
                continue

            if status == "not_supported":
                stats.not_supported += 1
                logger.info(
                    "not_supported metric_type=%s metric_date=%s detail=%s",
                    metric_type,
                    metric_date.isoformat(),
                    err,
                )
                continue

            stats.not_supported += 1
            logger.warning(
                "metric_error_nonfatal metric_type=%s metric_date=%s detail=%s",
                metric_type,
                metric_date.isoformat(),
                err,
            )

    return stats


def _connect_db() -> psycopg.Connection:
    return psycopg.connect(
        settings.db_url,
        options="-c timezone=Asia/Shanghai",
        row_factory=dict_row,
    )


def _load_sync_policy_context() -> SyncPolicyContext | None:
    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                  scs.connector_code,
                  scs.auto_sync_enabled,
                  scs.auto_sync_interval_minutes,
                  sco.enabled as connector_enabled,
                  sco.config_json
                from app.system_core_source scs
                left join app.system_connector_option sco
                  on sco.system_code = scs.system_code
                 and sco.connector_code = scs.connector_code
                where scs.system_code = 'health'
                """
            )
            row = cur.fetchone()

    if not row:
        return None

    connector_code = row.get("connector_code")
    if connector_code != "garmin_connect":
        return None

    if not row.get("connector_enabled"):
        return None

    config_json = row.get("config_json")
    if not isinstance(config_json, dict):
        config_json = {}

    return SyncPolicyContext(
        connector_code=connector_code,
        auto_sync_enabled=bool(row.get("auto_sync_enabled")),
        auto_sync_interval_minutes=max(int(row.get("auto_sync_interval_minutes") or 60), 15),
        config_json=config_json,
    )


def _coerce_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), minimum)


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _enqueue_auto_job_if_due(policy: SyncPolicyContext) -> None:
    if not policy.auto_sync_enabled:
        return

    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select exists(
                  select 1
                  from app.connector_sync_job
                  where system_code = 'health'
                    and status in ('queued', 'running')
                ) as has_pending
                """
            )
            has_pending = bool(cur.fetchone()["has_pending"])
            if has_pending:
                return

            cur.execute(
                """
                select triggered_at
                from app.connector_sync_job
                where system_code = 'health'
                  and job_type = 'auto_sync'
                order by triggered_at desc
                limit 1
                """
            )
            row = cur.fetchone()

            should_enqueue = False
            if not row:
                should_enqueue = True
            else:
                last_triggered_at = row["triggered_at"]
                next_trigger_at = last_triggered_at + timedelta(
                    minutes=policy.auto_sync_interval_minutes
                )
                should_enqueue = datetime.now(last_triggered_at.tzinfo) >= next_trigger_at

            if should_enqueue:
                cur.execute(
                    """
                    insert into app.connector_sync_job (
                      system_code,
                      connector_code,
                      job_type,
                      status,
                      triggered_at
                    ) values (
                      'health',
                      %s,
                      'auto_sync',
                      'queued',
                      now()
                    )
                    """,
                    (policy.connector_code,),
                )
                conn.commit()


def _claim_next_job(policy: SyncPolicyContext) -> SyncJob | None:
    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                with picked as (
                  select job_id
                  from app.connector_sync_job
                  where system_code = 'health'
                    and connector_code = %s
                    and status = 'queued'
                  order by triggered_at asc
                  for update skip locked
                  limit 1
                )
                update app.connector_sync_job
                set status = 'running',
                    started_at = now()
                where job_id in (select job_id from picked)
                returning
                  job_id::text as job_id,
                  connector_code,
                  job_type,
                  backfill_start_at,
                  backfill_end_at
                """,
                (policy.connector_code,),
            )
            row = cur.fetchone()

            if not row:
                conn.rollback()
                return None

            conn.commit()
            return SyncJob(
                job_id=row["job_id"],
                connector_code=row["connector_code"],
                job_type=row["job_type"],
                backfill_start_at=row["backfill_start_at"],
                backfill_end_at=row["backfill_end_at"],
            )


def _finish_job(*, job_id: str, status: str, error_message: str | None = None) -> None:
    with _connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update app.connector_sync_job
                set status = %s,
                    finished_at = now(),
                    error_message = %s
                where job_id = %s::uuid
                """,
                (status, error_message, job_id),
            )
        conn.commit()


def _build_metric_dates_for_job(
    *,
    job: SyncJob,
    timezone: ZoneInfo,
    fetch_window_days: int,
) -> list[date]:
    if job.job_type == "backfill_once":
        if not job.backfill_start_at or not job.backfill_end_at:
            raise RuntimeError("backfill_once job missing range")

        start_date = job.backfill_start_at.astimezone(timezone).date()
        end_date = job.backfill_end_at.astimezone(timezone).date()
        if start_date > end_date:
            raise RuntimeError("backfill_once range invalid")
        days = (end_date - start_date).days + 1
        return [start_date + timedelta(days=index) for index in range(days)]

    now_local_date = datetime.now(timezone).date()
    return _resolve_metric_dates(now_local_date, days=fetch_window_days)


def main() -> None:
    metrics = _resolve_metric_list()

    logger.info(
        "connector scheduler started poll_seconds=%s source_id=%s metrics=%s",
        settings.interval_seconds,
        settings.source_id,
        len(metrics),
    )

    with httpx.Client(timeout=settings.request_timeout_seconds) as http_client:
        while True:
            start = time.time()
            try:
                policy = _load_sync_policy_context()
                if not policy:
                    logger.debug("health core source not configured or disabled; skip")
                else:
                    _enqueue_auto_job_if_due(policy)
                    job = _claim_next_job(policy)
                    if job:
                        runtime_timezone_name = str(
                            policy.config_json.get("GARMIN_TIMEZONE", settings.garmin_timezone)
                        )
                        try:
                            runtime_timezone = ZoneInfo(runtime_timezone_name)
                        except Exception:
                            logger.warning(
                                "invalid GARMIN_TIMEZONE from config=%s, fallback=%s",
                                runtime_timezone_name,
                                settings.garmin_timezone,
                            )
                            runtime_timezone_name = settings.garmin_timezone
                            runtime_timezone = ZoneInfo(runtime_timezone_name)

                        runtime_fetch_window_days = _coerce_int(
                            policy.config_json.get(
                                "GARMIN_FETCH_WINDOW_DAYS",
                                settings.garmin_fetch_window_days,
                            ),
                            default=settings.garmin_fetch_window_days,
                            minimum=1,
                            maximum=90,
                        )
                        runtime_is_cn = _coerce_bool(
                            policy.config_json.get("GARMIN_IS_CN", settings.garmin_is_cn),
                            default=settings.garmin_is_cn,
                        )

                        metric_dates = _build_metric_dates_for_job(
                            job=job,
                            timezone=runtime_timezone,
                            fetch_window_days=runtime_fetch_window_days,
                        )

                        logger.info(
                            "job started job_id=%s job_type=%s date_range=%s..%s",
                            job.job_id,
                            job.job_type,
                            metric_dates[0].isoformat(),
                            metric_dates[-1].isoformat(),
                        )

                        stats = _run_cycle(
                            http_client,
                            timezone=runtime_timezone,
                            timezone_name=runtime_timezone_name,
                            runtime_is_cn=runtime_is_cn,
                            metrics=metrics,
                            metric_dates=metric_dates,
                        )
                        status = "success" if stats.errors == 0 else "failed"
                        error_message = None
                        if stats.errors > 0:
                            error_message = (
                                f"ingested={stats.ingested},no_data={stats.no_data},"
                                f"not_supported={stats.not_supported},errors={stats.errors}"
                            )

                        _finish_job(
                            job_id=job.job_id,
                            status=status,
                            error_message=error_message,
                        )
                        update_connector_health("ok" if stats.errors == 0 else "error")

                        logger.info(
                            "job finished job_id=%s status=%s ingested=%s no_data=%s not_supported=%s errors=%s",
                            job.job_id,
                            status,
                            stats.ingested,
                            stats.no_data,
                            stats.not_supported,
                            stats.errors,
                        )
            except Exception as exc:  # pragma: no cover - safety net
                logger.exception("scheduler loop crashed err=%s", exc)
                update_connector_health("error")

            elapsed = time.time() - start
            sleep_time = max(settings.interval_seconds - elapsed, 1)
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
