import type { components } from './types/dm-openapi.generated';

/** Pipeline statuses from DM scraper OpenAPI (`JobStatus`). */
export type ModalJobStatus = components['schemas']['JobStatus'];

export type FrontendScrapeStatus = 'queued' | 'processing' | 'completed' | 'failed';

/** Request body for `POST /jobs` — generated from committed OpenAPI snapshot. */
export type ModalScrapeJobRequest = components['schemas']['ScrapeJobRequest'];

/** `POST /jobs` response — generated. */
export type ModalCreateJobResponse = components['schemas']['ScrapeJobCreatedResponse'];

/** `GET /jobs/{job_id}` response — generated; some stacks still attach a seed `url`. */
export type ModalJobStatusResponse = components['schemas']['JobStatusResponse'] & {
  url?: string | null;
};

/** `GET /jobs` response — generated (`jobs[].id` is the canonical job id). */
export type ModalListJobsResponse = components['schemas']['ScrapeJobListResponse'];

export type ScrapeJobListItem = components['schemas']['ScrapeJobListItem'];

export interface FrontendScrapeJob {
  job_id: string;
  url: string;
  depth: number;
  status: FrontendScrapeStatus;
  backend_status: ModalJobStatus;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  progress?: number;
  current_step?: string;
  pages_scraped?: number;
  chunk_count?: number;
  embedding_count?: number;
  documents_created?: string[];
  error?: string;
}

export interface KnownScrapeJob {
  job_id: string;
  url: string;
  depth: number;
  created_at: string;
}

/** Resolve list-row id (`id` per OpenAPI; tolerate legacy `job_id` in mocks). */
export function remoteListJobId(row: ScrapeJobListItem | { id?: string; job_id?: string }): string {
  if (typeof row.id === 'string' && row.id) {
    return row.id;
  }
  const legacy = row as { job_id?: string };
  if (typeof legacy.job_id === 'string' && legacy.job_id) {
    return legacy.job_id;
  }
  return '';
}

export function mapModalStatusToFrontendStatus(status: ModalJobStatus): FrontendScrapeStatus {
  switch (status) {
    case 'pending':
    case 'validating':
      return 'queued';
    case 'completed':
      return 'completed';
    case 'failed':
    case 'cancelled':
      return 'failed';
    default:
      return 'processing';
  }
}

export function isModalTerminalStatus(status: ModalJobStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'cancelled';
}

export function clampNumber(value: number, minimum: number, maximum: number): number {
  return Math.min(Math.max(value, minimum), maximum);
}
