-- v0.4.0 development reset script
-- Purpose: clear business data only, keep auth/rbac/system source configuration.

begin;

-- 1) Clear core business schemas.
do $$
declare
  tbl record;
begin
  for tbl in
    select schemaname, tablename
    from pg_tables
    where schemaname in ('raw', 'canonical', 'domain_health', 'mart')
  loop
    execute format('truncate table %I.%I restart identity cascade', tbl.schemaname, tbl.tablename);
  end loop;
end $$;

-- 2) Clear annotation and runtime audit/job tables.
truncate table annotation.annotation restart identity cascade;
truncate table app.request_audit restart identity cascade;
truncate table app.connector_sync_job restart identity cascade;

-- keep app.connector_health single row, reset counters.
update app.connector_health
set last_run_at = null,
    last_status = 'never',
    success_count = 0,
    failure_count = 0,
    updated_at = now()
where id = 1;

insert into app.connector_health (id, last_status, success_count, failure_count)
values (1, 'never', 0, 0)
on conflict (id) do nothing;

commit;
