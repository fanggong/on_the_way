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

drop schema if exists mart_poc_signal cascade;
drop schema if exists domain_poc_signal cascade;
drop schema if exists mart_health cascade;

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

-- v0.3.1 POC retirement data cleanup.
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
comment on schema app is '应用支撑与审计层。';

comment on table raw.raw_event is '原始事件事实表，保存接入 payload 快照并用于幂等审计。';
comment on column raw.raw_event.raw_id is 'Raw 主键，唯一标识单条原始事件。';
comment on column raw.raw_event.source_id is '来源系统标识，例如 garmin_connect_health。';
comment on column raw.raw_event.external_id is '来源侧幂等外部键。';
comment on column raw.raw_event.occurred_at is '业务事件发生时间。';
comment on column raw.raw_event.payload_json is '原始业务 payload JSON。';
comment on column raw.raw_event.payload_hash is 'payload 哈希，用于幂等冲突校验。';
comment on column raw.raw_event.request_id is '请求审计 ID。';
comment on column raw.raw_event.ingested_at is '事件写入 Raw 的时间。';

comment on table annotation.annotation is '人工标注记录表，用于补充健康事件语义与标签。';
comment on column annotation.annotation.annotation_id is '标注记录主键。';
comment on column annotation.annotation.target_type is '标注目标类型（health_event/health_activity_event）。';
comment on column annotation.annotation.target_id is '标注目标 ID（随 target_type 解释）。';
comment on column annotation.annotation.label is '标注标签名。';
comment on column annotation.annotation.value is '标注标签值。';
comment on column annotation.annotation.created_at is '标注创建时间。';

comment on table app.request_audit is 'API 请求审计日志表，记录每次接入请求状态。';
comment on column app.request_audit.request_id is '请求唯一 ID。';
comment on column app.request_audit.source_id is '请求来源标识。';
comment on column app.request_audit.external_id is '来源外部幂等键。';
comment on column app.request_audit.received_at is '请求接收时间。';
comment on column app.request_audit.status is '处理状态（ok/error）。';
comment on column app.request_audit.error_code is '失败错误码。';
comment on column app.request_audit.message is '错误详情或审计消息。';
comment on column app.request_audit.created_at is '审计记录创建时间。';

comment on table app.connector_health is '连接器运行健康状态汇总表。';
comment on column app.connector_health.id is '固定单行主键（值=1）。';
comment on column app.connector_health.last_run_at is '最近一次连接器执行时间。';
comment on column app.connector_health.last_status is '最近一次执行状态。';
comment on column app.connector_health.success_count is '累计成功轮次。';
comment on column app.connector_health.failure_count is '累计失败轮次。';
comment on column app.connector_health.updated_at is '健康记录更新时间。';

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
