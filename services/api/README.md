# API Service (v0.1.0)

FastAPI service for `poc_signal` ingestion, annotation and query.

## Endpoints

- `POST /v1/ingest/manual-signal`
- `POST /v1/ingest/connector-signal`
- `POST /v1/annotation`
- `GET /v1/poc/signals`
- `GET /v1/poc/daily-summary`
- `GET /v1/health/connector`
- `GET /v1/health/live`

## Local Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
