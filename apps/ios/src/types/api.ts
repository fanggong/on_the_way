export type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error';

export type IngestManualRequest = {
  source_id: 'ios_manual';
  external_id: string;
  occurred_at: string;
  payload: {
    value: number;
    note?: string;
  };
};

export type IngestResponse = {
  status: 'ok';
  raw_id: string;
  ingested_at: string;
  idempotent: boolean;
};

export type DailySummary = {
  status: 'ok';
  stat_date: string;
  event_count: number;
  manual_count: number;
  connector_count: number;
  avg_value: number;
  min_value: number;
  max_value: number;
};

export type ApiError = {
  status: 'error';
  code: string;
  message: string;
  request_id: string;
};
