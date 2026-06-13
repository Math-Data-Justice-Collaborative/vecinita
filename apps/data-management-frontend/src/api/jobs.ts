import type { CreateJobResponse, Job } from "./types";

export interface JobsClientOptions {
  baseUrl: string;
  modalKey: string;
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
      "X-Vecinita-Proxy-Key": options.modalKey,
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
    headers: { "X-Vecinita-Proxy-Key": options.modalKey },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Get job failed (${String(response.status)})`);
  }
  return response.json() as Promise<Job>;
}

export function parseUrlsInput(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}
