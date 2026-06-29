import type { CreateJobResponse, Job, JobList, JobStatus } from "./types";

export interface JobsClientOptions {
  baseUrl: string;
  modalKey: string;
  accessToken?: string;
}

function jobsHeaders(options: JobsClientOptions): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Vecinita-Proxy-Key": options.modalKey,
  };
  if (options.accessToken) {
    headers.Authorization = `Bearer ${options.accessToken}`;
  }
  return headers;
}

export async function createJob(
  options: JobsClientOptions,
  urls: string[],
  chunkSizeTokens?: number,
): Promise<CreateJobResponse> {
  const body: { urls: string[]; options?: { chunk_size_tokens: number } } = {
    urls,
  };
  if (chunkSizeTokens !== undefined) {
    body.options = { chunk_size_tokens: chunkSizeTokens };
  }
  const response = await fetch(`${options.baseUrl}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...jobsHeaders(options),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Create job failed (${String(response.status)})`);
  }
  return response.json() as Promise<CreateJobResponse>;
}

export async function getJob(
  options: JobsClientOptions,
  jobId: string,
): Promise<Job> {
  const response = await fetch(`${options.baseUrl}/jobs/${jobId}`, {
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Get job failed (${String(response.status)})`);
  }
  return response.json() as Promise<Job>;
}

export async function listJobs(
  options: JobsClientOptions,
  status?: JobStatus,
): Promise<Job[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await fetch(`${options.baseUrl}/jobs${query}`, {
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `List jobs failed (${String(response.status)})`);
  }
  const body = (await response.json()) as JobList;
  return body.jobs;
}

export function parseUrlsInput(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}
