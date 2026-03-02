export class ApiError extends Error {
  code: string;
  status: number;
  requestId?: string;

  constructor(message: string, code: string, status: number, requestId?: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://localhost:8000';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

interface RequestOptions {
  method?: HttpMethod;
  token?: string | null;
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers,
    credentials: 'include',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const raw = await response.text();
  const json = raw ? JSON.parse(raw) : null;

  if (!response.ok || json?.status === 'error') {
    throw new ApiError(
      json?.message ?? `request failed with status ${response.status}`,
      json?.code ?? 'HTTP_ERROR',
      response.status,
      json?.request_id,
    );
  }

  if (json && json.status === 'ok' && Object.prototype.hasOwnProperty.call(json, 'data')) {
    return json.data as T;
  }

  return json as T;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}
