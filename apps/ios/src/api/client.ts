import type {ApiError, DailySummary, IngestManualRequest, IngestResponse} from '../types/api';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

async function parseResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ApiError;

  if (!response.ok) {
    const err = body as ApiError;
    throw new Error(`${err.code}: ${err.message}`);
  }

  return body as T;
}

export async function ingestManualSignal(payload: IngestManualRequest): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/ingest/manual-signal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<IngestResponse>(response);
}

export async function fetchDailySummary(date: string): Promise<DailySummary> {
  const response = await fetch(`${API_BASE_URL}/v1/poc/daily-summary?date=${date}`);
  return parseResponse<DailySummary>(response);
}
