# API Service (v0.4.0)

Version status: `accepted` (`2026-03-02`)

FastAPI service for:
- auth/profile/RBAC
- system source management and sync jobs
- health connector ingest + health query APIs

## Endpoint Groups

- Auth: `/v1/auth/*`
- Profile: `/v1/profile/me`
- RBAC: `/v1/rbac/*`
- System sources: `/v1/system-sources/*`
- Health query/config: `/v1/health/*`
- Ingest and annotation: `/v1/ingest/connector-health`, `/v1/annotation`

## Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
