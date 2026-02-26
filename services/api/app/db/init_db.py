from __future__ import annotations

from sqlalchemy import text

from app.db.session import engine

INIT_SQL = """
create schema if not exists public;
set search_path = public, pg_catalog;
create extension if not exists pgcrypto with schema public;

create schema if not exists raw;
create schema if not exists canonical;
create schema if not exists domain_poc_signal;
create schema if not exists mart_poc_signal;
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
  target_id uuid not null,
  label text not null,
  value text not null,
  created_at timestamptz not null default now()
);

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
"""



def init_database() -> None:
    with engine.begin() as conn:
        conn.execute(text(INIT_SQL))
