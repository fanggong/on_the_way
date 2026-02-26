# OpenMetadata Local Notes

This compose setup includes OpenMetadata server + ingestion + required MySQL and Elasticsearch dependencies.

After startup, open:
- UI: http://localhost:8585
- API: http://localhost:8585/api

If OpenMetadata startup fails due to memory limits, increase Docker resources and restart only metadata services.
