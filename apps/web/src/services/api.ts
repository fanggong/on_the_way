import { requestJson } from './http';

export interface SessionUser {
  user_id: string;
  email: string;
  roles: string[];
}

export interface SessionResult {
  access_token: string;
  expires_in: number;
  profile_completed: boolean;
  user: SessionUser;
}

export interface AuthMeResult {
  user_id: string;
  email: string;
  roles: string[];
  permissions: string[];
  profile_completed: boolean;
}

export interface ProfileData {
  user_id: string;
  display_name: string;
  timezone: string;
  gender: string | null;
  birth_date: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  profile_completed: boolean;
}

export interface ConnectorOption {
  connector_code: string;
  display_name: string;
  enabled: boolean;
  updated_at: string | null;
}

export interface SyncPolicy {
  connector_code: string | null;
  auto_sync_enabled: boolean;
  auto_sync_interval_minutes: number;
  updated_at: string | null;
}

export interface SyncJob {
  job_id: string;
  system_code: string;
  connector_code: string;
  job_type: string;
  status: string;
  backfill_start_at: string | null;
  backfill_end_at: string | null;
  triggered_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
}

export interface SystemSourceItem {
  system_code: string;
  system_name: string;
  available_connectors: ConnectorOption[];
  core_source: SyncPolicy;
  latest_job: SyncJob | null;
}

export interface PagedResult<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface ConnectorHealthSummary {
  last_run_at: string | null;
  last_status: string;
  success_count: number;
  failure_count: number;
}

export async function registerUser(email: string, password: string): Promise<{ user_id: string; email: string }> {
  return requestJson('/v1/auth/register', {
    method: 'POST',
    body: { email, password },
  });
}

export async function loginUser(email: string, password: string): Promise<SessionResult> {
  return requestJson('/v1/auth/login', {
    method: 'POST',
    body: { email, password },
  });
}

export async function refreshSession(): Promise<SessionResult> {
  return requestJson('/v1/auth/refresh', {
    method: 'POST',
  });
}

export async function logoutSession(): Promise<{ logged_out: boolean }> {
  return requestJson('/v1/auth/logout', {
    method: 'POST',
  });
}

export async function getAuthMe(token: string): Promise<AuthMeResult> {
  return requestJson('/v1/auth/me', { token });
}

export async function getMyProfile(token: string): Promise<ProfileData> {
  return requestJson('/v1/profile/me', { token });
}

export async function updateMyProfile(
  token: string,
  payload: {
    display_name: string;
    timezone: string;
    gender: string | null;
    birth_date: string | null;
    height_cm: number | null;
    weight_kg: number | null;
  },
): Promise<ProfileData> {
  return requestJson('/v1/profile/me', {
    method: 'PUT',
    token,
    body: payload,
  });
}

export async function getSystemSources(token: string): Promise<{ items: SystemSourceItem[] }> {
  return requestJson('/v1/system-sources', { token });
}

export async function updateCoreSource(token: string, systemCode: string, connectorCode: string): Promise<SyncPolicy> {
  return requestJson(`/v1/system-sources/${systemCode}/core-source`, {
    method: 'PUT',
    token,
    body: { connector_code: connectorCode },
  });
}

export async function updateConnectorEnabled(
  token: string,
  systemCode: string,
  connectorCode: string,
  enabled: boolean,
): Promise<void> {
  await requestJson(`/v1/system-sources/${systemCode}/connectors/${connectorCode}`, {
    method: 'PUT',
    token,
    body: { enabled },
  });
}

export async function getSyncPolicy(token: string, systemCode: string): Promise<SyncPolicy> {
  return requestJson(`/v1/system-sources/${systemCode}/sync-policy`, { token });
}

export async function updateSyncPolicy(
  token: string,
  systemCode: string,
  payload: { auto_sync_enabled: boolean; auto_sync_interval_minutes: number },
): Promise<SyncPolicy> {
  return requestJson(`/v1/system-sources/${systemCode}/sync-policy`, {
    method: 'PUT',
    token,
    body: payload,
  });
}

export async function createBackfillJob(
  token: string,
  systemCode: string,
  payload: {
    backfill_start_at: string;
    backfill_end_at: string;
  },
): Promise<SyncJob> {
  return requestJson(`/v1/system-sources/${systemCode}/sync-jobs`, {
    method: 'POST',
    token,
    body: {
      job_type: 'backfill_once',
      backfill_start_at: payload.backfill_start_at,
      backfill_end_at: payload.backfill_end_at,
    },
  });
}

export async function getSyncJobs(token: string, systemCode: string): Promise<{ items: SyncJob[] }> {
  return requestJson(`/v1/system-sources/${systemCode}/sync-jobs`, { token });
}

export async function getHealthConnectorConfig(token: string): Promise<{
  GARMIN_FETCH_WINDOW_DAYS: number;
  GARMIN_BACKFILL_DAYS: number;
  GARMIN_TIMEZONE: string;
  GARMIN_IS_CN: boolean;
}> {
  return requestJson('/v1/health/connectors/config', { token });
}

export async function updateHealthConnectorConfig(
  token: string,
  payload: {
    GARMIN_FETCH_WINDOW_DAYS: number;
    GARMIN_BACKFILL_DAYS: number;
    GARMIN_TIMEZONE: string;
    GARMIN_IS_CN: boolean;
  },
): Promise<{
  GARMIN_FETCH_WINDOW_DAYS: number;
  GARMIN_BACKFILL_DAYS: number;
  GARMIN_TIMEZONE: string;
  GARMIN_IS_CN: boolean;
}> {
  return requestJson('/v1/health/connectors/config', {
    method: 'PUT',
    token,
    body: payload,
  });
}

export async function queryHealthDomainMetrics(
  token: string,
  query: {
    start_date: string;
    end_date: string;
    metric_name?: string;
    account_ref?: string;
    page?: number;
    page_size?: number;
  },
): Promise<PagedResult<Record<string, unknown>>> {
  return requestJson('/v1/health/domain/metrics', {
    token,
    query,
  });
}

export async function queryHealthMartOverview(
  token: string,
  query: {
    start_date?: string;
    end_date?: string;
    account_ref?: string;
    page?: number;
    page_size?: number;
  },
): Promise<PagedResult<Record<string, unknown>>> {
  return requestJson('/v1/health/mart/overview', {
    token,
    query,
  });
}

export async function queryHealthMartMetricSummary(
  token: string,
  query: {
    start_date?: string;
    end_date?: string;
    account_ref?: string;
    page?: number;
    page_size?: number;
  },
): Promise<PagedResult<Record<string, unknown>>> {
  return requestJson('/v1/health/mart/metric-summary', {
    token,
    query,
  });
}

export async function queryHealthMartActivityTopics(
  token: string,
  query: {
    start_date?: string;
    end_date?: string;
    account_ref?: string;
    page?: number;
    page_size?: number;
  },
): Promise<PagedResult<Record<string, unknown>>> {
  return requestJson('/v1/health/mart/activity-topics', {
    token,
    query,
  });
}

export async function getConnectorHealthSummary(): Promise<ConnectorHealthSummary> {
  return requestJson('/v1/health/connector');
}
