from __future__ import annotations

from sqlalchemy import text

from app.db.session import engine

INIT_SQL = """
create schema if not exists public;
set search_path = public, pg_catalog;
set timezone = 'Asia/Shanghai';
create extension if not exists pgcrypto with schema public;

create schema if not exists raw;
create schema if not exists canonical;
create schema if not exists mart;
create schema if not exists annotation;
create schema if not exists app;

create schema if not exists domain_health;
create schema if not exists domain_time;
create schema if not exists domain_income;
create schema if not exists domain_finance;
create schema if not exists domain_ability;
create schema if not exists domain_relationship;
create schema if not exists domain_life;
create schema if not exists domain_security;

create table if not exists raw.raw_event (
  raw_id uuid primary key default public.gen_random_uuid(),
  source_id text not null,
  external_id text not null,
  occurred_at timestamptz not null,
  payload_json jsonb not null,
  payload_hash text not null,
  request_id uuid not null,
  ingested_at timestamptz not null default now(),
  unique (source_id, external_id)
);

create index if not exists idx_raw_event_occurred_at on raw.raw_event(occurred_at);
create index if not exists idx_raw_event_source on raw.raw_event(source_id);

create table if not exists annotation.annotation (
  annotation_id uuid primary key default public.gen_random_uuid(),
  target_type text not null,
  target_id text not null,
  label text not null,
  value text not null,
  created_at timestamptz not null default now()
);

alter table annotation.annotation
  alter column target_id type text
  using target_id::text;

create table if not exists app.request_audit (
  request_id uuid primary key,
  source_id text not null,
  external_id text not null,
  received_at timestamptz not null,
  status text not null,
  error_code text,
  message text,
  created_at timestamptz not null default now()
);

create table if not exists app.connector_health (
  id int primary key,
  last_run_at timestamptz,
  last_status text not null,
  success_count bigint not null default 0,
  failure_count bigint not null default 0,
  updated_at timestamptz not null default now(),
  check (id = 1)
);

insert into app.connector_health (id, last_status, success_count, failure_count)
values (1, 'never', 0, 0)
on conflict (id) do nothing;

create table if not exists app.user_account (
  user_id uuid primary key default public.gen_random_uuid(),
  email text not null unique,
  password_hash text not null,
  status text not null default 'active' check (status in ('active', 'disabled')),
  profile_completed boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (email = lower(trim(email)))
);

create table if not exists app.user_profile (
  user_id uuid primary key references app.user_account(user_id) on delete cascade,
  display_name text not null,
  timezone text not null default 'Asia/Shanghai',
  gender text,
  birth_date date,
  height_cm numeric(6,2),
  weight_kg numeric(6,2),
  updated_at timestamptz not null default now()
);

create table if not exists app.user_session (
  session_id uuid primary key default public.gen_random_uuid(),
  user_id uuid not null references app.user_account(user_id) on delete cascade,
  refresh_token_hash text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_user_session_user_id on app.user_session(user_id);
create index if not exists idx_user_session_expires_at on app.user_session(expires_at);

create table if not exists app.rbac_role (
  role_code text primary key,
  display_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists app.rbac_permission (
  permission_code text primary key,
  display_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists app.rbac_role_permission (
  role_code text not null references app.rbac_role(role_code) on delete cascade,
  permission_code text not null references app.rbac_permission(permission_code) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (role_code, permission_code)
);

create table if not exists app.rbac_user_role (
  user_id uuid not null references app.user_account(user_id) on delete cascade,
  role_code text not null references app.rbac_role(role_code) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, role_code)
);

create table if not exists app.system_connector_option (
  system_code text not null,
  connector_code text not null,
  display_name text not null,
  enabled boolean not null default true,
  config_json jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (system_code, connector_code)
);

create table if not exists app.system_core_source (
  system_code text primary key,
  connector_code text,
  auto_sync_enabled boolean not null default false,
  auto_sync_interval_minutes int not null default 60 check (auto_sync_interval_minutes between 15 and 1440),
  updated_by uuid,
  updated_at timestamptz not null default now(),
  constraint fk_system_core_source_connector
    foreign key (system_code, connector_code)
    references app.system_connector_option(system_code, connector_code)
);

create table if not exists app.connector_sync_job (
  job_id uuid primary key default public.gen_random_uuid(),
  system_code text not null,
  connector_code text not null,
  job_type text not null check (job_type in ('backfill_once', 'auto_sync')),
  backfill_start_at timestamptz,
  backfill_end_at timestamptz,
  status text not null check (status in ('queued', 'running', 'success', 'failed', 'canceled')),
  triggered_by uuid,
  triggered_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  error_message text,
  check (
    (job_type = 'backfill_once' and backfill_start_at is not null and backfill_end_at is not null and backfill_start_at <= backfill_end_at)
    or (job_type = 'auto_sync')
  ),
  constraint fk_sync_job_connector
    foreign key (system_code, connector_code)
    references app.system_connector_option(system_code, connector_code)
);

create index if not exists idx_connector_sync_job_system_status
  on app.connector_sync_job(system_code, status, triggered_at desc);
create index if not exists idx_connector_sync_job_triggered_at
  on app.connector_sync_job(triggered_at desc);

insert into app.rbac_role (role_code, display_name)
values
  ('super_admin', '超级管理员'),
  ('admin', '管理员'),
  ('analyst', '分析师'),
  ('viewer', '访客')
on conflict (role_code) do nothing;

insert into app.rbac_permission (permission_code, display_name)
values
  ('profile.write', '个人资料写入'),
  ('health.connector.write', '健康连接器配置写入'),
  ('health.domain.read', '健康 Domain 查询'),
  ('health.mart.read', '健康 Mart 查询'),
  ('system_source.write', '系统数据源管理写入'),
  ('rbac.user_role.write', '用户角色分配写入')
on conflict (permission_code) do nothing;

insert into app.rbac_role_permission (role_code, permission_code)
values
  ('super_admin', 'profile.write'),
  ('super_admin', 'health.connector.write'),
  ('super_admin', 'health.domain.read'),
  ('super_admin', 'health.mart.read'),
  ('super_admin', 'system_source.write'),
  ('super_admin', 'rbac.user_role.write'),

  ('admin', 'profile.write'),
  ('admin', 'health.connector.write'),
  ('admin', 'health.domain.read'),
  ('admin', 'health.mart.read'),
  ('admin', 'system_source.write'),

  ('analyst', 'profile.write'),
  ('analyst', 'health.domain.read'),
  ('analyst', 'health.mart.read'),

  ('viewer', 'profile.write'),
  ('viewer', 'health.mart.read')
on conflict (role_code, permission_code) do nothing;

insert into app.system_connector_option (
  system_code,
  connector_code,
  display_name,
  enabled,
  config_json,
  updated_at
)
values (
  'health',
  'garmin_connect',
  'Garmin Connect',
  true,
  jsonb_build_object(
    'GARMIN_FETCH_WINDOW_DAYS', 3,
    'GARMIN_BACKFILL_DAYS', 10,
    'GARMIN_TIMEZONE', 'Asia/Shanghai',
    'GARMIN_IS_CN', true
  ),
  now()
)
on conflict (system_code, connector_code) do nothing;

-- v0.3.1 and v0.4.0 backward-cleanup for old POC traces.
drop schema if exists mart_poc_signal cascade;
drop schema if exists domain_poc_signal cascade;
drop schema if exists mart_health cascade;

delete from annotation.annotation
where target_type = 'signal_event';

delete from app.request_audit
where source_id in ('ios_manual', 'signal_random_connector');

delete from raw.raw_event
where source_id in ('ios_manual', 'signal_random_connector');

comment on schema raw is 'Raw 原始事实层。';
comment on schema canonical is 'Canonical 标准化层。';
comment on schema domain_health is '健康系统 Domain 领域事实层。';
comment on schema mart is '统一 Mart 消费层。';
comment on schema annotation is '人工标注层。';
comment on schema app is '应用支撑与治理层。';

comment on table app.user_account is '账号主体表（邮箱+密码哈希+状态）。';
comment on table app.user_profile is '用户个人资料表（首次登录完善信息）。';
comment on table app.user_session is '刷新令牌会话表。';
comment on table app.rbac_role is 'RBAC 角色定义表。';
comment on table app.rbac_permission is 'RBAC 权限定义表。';
comment on table app.rbac_role_permission is '角色与权限映射表。';
comment on table app.rbac_user_role is '用户与角色映射表。';
comment on table app.system_connector_option is '系统可选连接器配置表。';
comment on table app.system_core_source is '系统核心数据源与自动同步策略表。';
comment on table app.connector_sync_job is '连接器同步任务表（自动同步+单次回填）。';

comment on table raw.raw_event is '原始事件事实表，保存接入 payload 快照并用于幂等审计。';
comment on table annotation.annotation is '人工标注记录表，用于补充健康事件语义与标签。';
comment on table app.request_audit is 'API 请求审计日志表，记录每次接入请求状态。';
comment on table app.connector_health is '连接器运行健康状态汇总表。';

do $$
declare
  db_name text := current_database();
begin
  execute format('alter database %I set timezone to %L', db_name, 'Asia/Shanghai');
end $$;
"""


def init_database() -> None:
    with engine.begin() as conn:
        conn.execute(text(INIT_SQL))
