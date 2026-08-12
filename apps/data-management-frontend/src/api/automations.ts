/**
 * F75 automations config + run history via write-API.
 * [Corpus: feature-list.md §F75]
 * [Spec: docs/api-contract.md §EV-027 Automations]
 * [Corpus: user-journeys.md §UJ-080]
 */

import type { CorpusClientOptions } from "./corpus";

export type AutomationJobType = "automation_catchup" | "freshness_refresh";

export type AutomationRunStatus =
  "pending" | "running" | "completed" | "failed" | "skipped" | "blocked";

/** Wire format from GET/PATCH /internal/v1/automations/config */
export interface AutomationsConfig {
  enabled: boolean;
  kill_switch: boolean;
  max_concurrent: number;
}

/** Wire format from GET /internal/v1/automations/runs item */
export interface AutomationRun {
  id: string;
  job_type: AutomationJobType;
  status: AutomationRunStatus;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  document_id: string | null;
  revision: string | null;
  created_at: string;
  updated_at: string;
}

export interface AutomationRunListResponse {
  items: AutomationRun[];
  page: number;
  page_size: number;
  total_count: number;
}

function authHeader(options: CorpusClientOptions): string {
  return `Bearer ${options.accessToken ?? options.apiKey ?? ""}`;
}

export async function fetchAutomationsConfig(
  options: CorpusClientOptions,
): Promise<AutomationsConfig> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/automations/config`,
    {
      headers: {
        Authorization: authHeader(options),
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Automations config failed (${String(response.status)})`);
  }
  return (await response.json()) as AutomationsConfig;
}

export async function patchAutomationsEnabled(
  options: CorpusClientOptions,
  enabled: boolean,
): Promise<AutomationsConfig> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/automations/config`,
    {
      method: "PATCH",
      headers: {
        Authorization: authHeader(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ enabled }),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Automations config update failed (${String(response.status)})`,
    );
  }
  return (await response.json()) as AutomationsConfig;
}

export async function fetchAutomationRuns(
  options: CorpusClientOptions,
  params?: { page?: number; page_size?: number },
): Promise<AutomationRunListResponse> {
  const query = new URLSearchParams({
    page: String(params?.page ?? 1),
    page_size: String(params?.page_size ?? 20),
  });
  const response = await fetch(
    `${options.baseUrl}/internal/v1/automations/runs?${query.toString()}`,
    {
      headers: {
        Authorization: authHeader(options),
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Automation runs failed (${String(response.status)})`);
  }
  return (await response.json()) as AutomationRunListResponse;
}
