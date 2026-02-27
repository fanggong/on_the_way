# API Service (v0.3.1)

Version status: `accepted` (`2026-02-27`)

FastAPI service for health connector ingest, annotation, and service health checks.

## Endpoints

- `POST /v1/ingest/connector-health`
- `POST /v1/annotation`
- `GET /v1/health/connector`
- `GET /v1/health/live`

## Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
