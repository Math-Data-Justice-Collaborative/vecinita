/**
 * F77 LoRA fine-tune client — approve, eval, promote/rollback (UJ-082).
 * [Corpus: feature-list.md §F77]
 * [Spec: docs/api-contract.md §EV-027 Fine-tune]
 * [Corpus: user-journeys.md §UJ-082]
 */

import type { CorpusClientOptions } from "./corpus";
import type { JobsClientOptions } from "./jobs";
import type { CreateJobResponse, Job } from "./types";

export interface FinetuneSideMetrics {
  faithfulness: number | null;
  answer_relevancy: number | null;
  questions_scored: number;
}

export interface FinetuneEvalReport {
  run_id: string;
  adapter_id: string;
  base_model_id: string;
  base: FinetuneSideMetrics;
  adapter: FinetuneSideMetrics;
  /** Always false — promote is human judgment only (AC-FT4). */
  auto_promote: boolean;
  summary: string;
}

export interface FinetuneAdapterPin {
  adapter_id: string | null;
  base: boolean;
}

export interface FinetunePromoteResponse {
  promoted: boolean;
  adapter_id: string | null;
  base: boolean;
  /** Always false — never automated (AC-FT4). */
  auto_promote: boolean;
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

function corpusAuth(options: CorpusClientOptions): string {
  return `Bearer ${options.accessToken ?? options.apiKey ?? ""}`;
}

export async function createFinetuneTrainJob(
  options: JobsClientOptions,
): Promise<CreateJobResponse> {
  const response = await fetch(`${options.baseUrl}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...jobsHeaders(options),
    },
    body: JSON.stringify({
      urls: [],
      options: { job_type: "finetune_train" },
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Create finetune job failed (${String(response.status)})`,
    );
  }
  return (await response.json()) as CreateJobResponse;
}

export async function approveFinetuneJob(
  options: JobsClientOptions,
  jobId: string,
): Promise<Job> {
  const response = await fetch(`${options.baseUrl}/jobs/${jobId}/approve`, {
    method: "POST",
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Approve finetune job failed (${String(response.status)})`,
    );
  }
  return (await response.json()) as Job;
}

export async function listFinetuneJobs(
  options: JobsClientOptions,
): Promise<Job[]> {
  const response = await fetch(`${options.baseUrl}/jobs`, {
    headers: jobsHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `List finetune jobs failed (${String(response.status)})`,
    );
  }
  const body = (await response.json()) as { jobs: Job[] };
  return body.jobs.filter((job) => job.job_type === "finetune_train");
}

export async function fetchFinetuneEval(
  options: CorpusClientOptions,
  runId: string,
): Promise<FinetuneEvalReport> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/finetune/runs/${runId}/eval`,
    {
      headers: {
        Authorization: corpusAuth(options),
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Finetune eval failed (${String(response.status)})`);
  }
  return (await response.json()) as FinetuneEvalReport;
}

export async function fetchFinetuneAdapterPin(
  options: CorpusClientOptions,
): Promise<FinetuneAdapterPin> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/finetune/adapter`,
    {
      headers: {
        Authorization: corpusAuth(options),
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Finetune adapter pin failed (${String(response.status)})`);
  }
  return (await response.json()) as FinetuneAdapterPin;
}

export async function promoteFinetuneAdapter(
  options: CorpusClientOptions,
  adapterId: string,
): Promise<FinetunePromoteResponse> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/finetune/promote`,
    {
      method: "POST",
      headers: {
        Authorization: corpusAuth(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ adapter_id: adapterId }),
    },
  );
  if (!response.ok) {
    throw new Error(`Promote failed (${String(response.status)})`);
  }
  return (await response.json()) as FinetunePromoteResponse;
}

export async function rollbackFinetuneAdapter(
  options: CorpusClientOptions,
): Promise<FinetunePromoteResponse> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/finetune/promote`,
    {
      method: "POST",
      headers: {
        Authorization: corpusAuth(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ rollback: true }),
    },
  );
  if (!response.ok) {
    throw new Error(`Rollback failed (${String(response.status)})`);
  }
  return (await response.json()) as FinetunePromoteResponse;
}
