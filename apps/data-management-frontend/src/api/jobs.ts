import type { CreateJobResponse, Job, JobList, JobStatus } from "./types";

export interface JobsClientOptions {
  baseUrl: string;
  modalKey: string;
  accessToken?: string | undefined;
}

export interface JobEventHandlers {
  onJob: (job: Job) => void;
  onError?: ((error: unknown) => void) | undefined;
  lastEventId?: string | undefined;
}

export interface JobEventSubscription {
  close: () => void;
}

function jobsHeaders(
  options: JobsClientOptions,
  extra?: Record<string, string>,
): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Vecinita-Proxy-Key": options.modalKey,
    ...extra,
  };
  if (options.accessToken) {
    headers["Authorization"] = `Bearer ${options.accessToken}`;
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

export async function cancelJob(
  options: JobsClientOptions,
  jobId: string,
): Promise<Job> {
  const response = await fetch(`${options.baseUrl}/jobs/${jobId}/cancel`, {
    method: "POST",
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Cancel job failed (${String(response.status)})`);
  }
  return response.json() as Promise<Job>;
}

export async function retryJob(
  options: JobsClientOptions,
  jobId: string,
): Promise<CreateJobResponse> {
  const response = await fetch(`${options.baseUrl}/jobs/${jobId}/retry`, {
    method: "POST",
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Retry job failed (${String(response.status)})`);
  }
  return response.json() as Promise<CreateJobResponse>;
}

export async function deleteJob(
  options: JobsClientOptions,
  jobId: string,
): Promise<void> {
  const response = await fetch(`${options.baseUrl}/jobs/${jobId}`, {
    method: "DELETE",
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Delete job failed (${String(response.status)})`);
  }
}

/**
 * Subscribe to Modal `GET /jobs/events` via fetch streaming (auth headers required;
 * native EventSource cannot set Bearer / proxy key — RD-173 / TP-S013-01).
 */
export function subscribeJobEvents(
  options: JobsClientOptions,
  handlers: JobEventHandlers,
): JobEventSubscription {
  const controller = new AbortController();
  void readJobEventStream(options, handlers, controller.signal);
  return {
    close: () => {
      controller.abort();
    },
  };
}

async function readJobEventStream(
  options: JobsClientOptions,
  handlers: JobEventHandlers,
  signal: AbortSignal,
): Promise<void> {
  try {
    const headers = jobsHeaders(options, {
      Accept: "text/event-stream",
      "Cache-Control": "no-cache",
    });
    if (handlers.lastEventId) {
      headers["Last-Event-ID"] = handlers.lastEventId;
    }
    const response = await fetch(`${options.baseUrl}/jobs/events`, {
      headers,
      signal,
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(
        detail || `Job events failed (${String(response.status)})`,
      );
    }
    if (!response.body) {
      throw new Error("No response body from /jobs/events");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let eventName = "message";
    let dataLines: string[] = [];

    const flush = (): void => {
      if (dataLines.length === 0) {
        eventName = "message";
        return;
      }
      const raw = dataLines.join("\n");
      dataLines = [];
      const name = eventName;
      eventName = "message";
      if (name !== "job" && name !== "message") {
        return;
      }
      try {
        handlers.onJob(JSON.parse(raw) as Job);
      } catch (err) {
        handlers.onError?.(err);
      }
    };

    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // String.split always yields ≥1 element; avoid ?? which leaves an uncovered arm.
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- split remainder
      buffer = lines.pop()!;
      for (const line of lines) {
        if (line === "") {
          flush();
          continue;
        }
        if (line.startsWith(":")) {
          continue;
        }
        if (line.startsWith("id:")) {
          continue;
        }
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
          continue;
        }
        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }
      }
    }
    flush();
  } catch (err) {
    if (signal.aborted) {
      return;
    }
    handlers.onError?.(err);
  }
}

export function parseUrlsInput(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}
