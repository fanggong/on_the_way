select
  source_id,
  external_id,
  count(*) as dup_count
from raw.raw_event
group by source_id, external_id
having count(*) > 1
