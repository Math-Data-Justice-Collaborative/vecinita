import type { TagInput } from "./types";
import type { CorpusClientOptions } from "./corpus";

/** Wire format from GET /internal/v1/stats/summary — docs/api-contract.md */
export interface StatsSummaryApiResponse {
  total_documents: number;
  total_chunks: number;
  tag_distribution: { slug: string; label: string; document_count: number }[];
  language_breakdown: Record<string, number>;
  recent_activity: {
    event_type: string;
    entity_id: string;
    created_at: string;
    summary?: string | null;
  }[];
  top_served: {
    document_id: string;
    title: string | null;
    served_count: number;
    url?: string | null;
    last_served_at?: string | null;
  }[];
}

export interface StatsSummary {
  total_documents: number;
  total_chunks: number;
  tag_distribution: { tag: string; count: number }[];
  language_breakdown: { language: string; count: number }[];
  recent_activity: {
    event_type: string;
    entity_type: string;
    entity_id: string;
    timestamp: string;
    summary: string | null;
  }[];
  top_served: {
    document_id: string;
    title: string | null;
    served_count: number;
  }[];
}

function entityTypeFromEventType(eventType: string): string {
  const dot = eventType.indexOf(".");
  return dot >= 0 ? eventType.slice(0, dot) : eventType;
}

/** Normalized for DashboardPage rendering. */
export function parseStatsSummary(raw: StatsSummaryApiResponse): StatsSummary {
  return {
    total_documents: raw.total_documents,
    total_chunks: raw.total_chunks,
    tag_distribution: raw.tag_distribution.map((row) => ({
      tag: row.label || row.slug,
      count: row.document_count,
    })),
    language_breakdown: Object.entries(raw.language_breakdown).map(
      ([language, count]) => ({
        language,
        count,
      }),
    ),
    recent_activity: raw.recent_activity.map((row) => ({
      event_type: row.event_type,
      entity_type: entityTypeFromEventType(row.event_type),
      entity_id: row.entity_id,
      timestamp: row.created_at,
      summary: row.summary ?? null,
    })),
    top_served: raw.top_served.map((row) => ({
      document_id: row.document_id,
      title: row.title,
      served_count: row.served_count,
    })),
  };
}

/** Wire format from GET /internal/v1/health/all — docs/api-contract.md */
export interface HealthAggregateApiResponse {
  status: "healthy" | "degraded";
  services: Record<
    string,
    { status: "up" | "down"; latency_ms: number | null; error: string | null }
  >;
  checked_at: string;
}

export interface ServiceHealth {
  name: string;
  status: "healthy" | "unhealthy";
  latency_ms: number | null;
  error: string | null;
}

/** Normalized for HealthPage rendering. */
export interface HealthAggregate {
  overall: "healthy" | "degraded";
  services: ServiceHealth[];
  checked_at: string;
}

export function parseHealthAggregate(
  raw: HealthAggregateApiResponse,
): HealthAggregate {
  return {
    overall: raw.status,
    checked_at: raw.checked_at,
    services: Object.entries(raw.services).map(([name, svc]) => ({
      name,
      status: svc.status === "up" ? "healthy" : "unhealthy",
      latency_ms: svc.latency_ms,
      error: svc.error,
    })),
  };
}

export async function fetchStatsSummary(
  options: CorpusClientOptions,
): Promise<StatsSummary> {
  const response = await fetch(`${options.baseUrl}/internal/v1/stats/summary`, {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Stats summary failed (${String(response.status)})`);
  }
  const raw = (await response.json()) as StatsSummaryApiResponse;
  return parseStatsSummary(raw);
}

export async function fetchHealthAggregate(
  options: CorpusClientOptions,
): Promise<HealthAggregate> {
  const response = await fetch(`${options.baseUrl}/internal/v1/health/all`, {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Health check failed (${String(response.status)})`);
  }
  const raw = (await response.json()) as HealthAggregateApiResponse;
  return parseHealthAggregate(raw);
}

export interface BulkResult {
  successes: string[];
  failures: { document_id: string; error: string }[];
}

export async function bulkDeleteDocuments(
  options: CorpusClientOptions,
  documentIds: string[],
): Promise<BulkResult> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/bulk`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ document_ids: documentIds }),
    },
  );
  if (!response.ok)
    throw new Error(`Bulk delete failed (${String(response.status)})`);
  return response.json() as Promise<BulkResult>;
}

export async function bulkTagDocuments(
  options: CorpusClientOptions,
  documentIds: string[],
  addTags: TagInput[],
  removeSlugs: string[],
): Promise<BulkResult> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/bulk/tags`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        document_ids: documentIds,
        add: addTags,
        remove: removeSlugs,
      }),
    },
  );
  if (!response.ok)
    throw new Error(`Bulk tag failed (${String(response.status)})`);
  return response.json() as Promise<BulkResult>;
}

/** Wire format from GET /internal/v1/audit — docs/api-contract.md */
export interface AuditLogEntryApi {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  request_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogResponseApi {
  items: AuditLogEntryApi[];
  page: number;
  page_size: number;
  total_count: number;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

/** Normalized for AuditPage rendering. */
export interface AuditPage {
  events: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
}

export function parseAuditLogResponse(raw: AuditLogResponseApi): AuditPage {
  return {
    page: raw.page,
    page_size: raw.page_size,
    total: raw.total_count,
    events: raw.items.map((item) => ({
      id: item.id,
      event_type: item.event_type,
      entity_type: item.entity_type,
      entity_id: item.entity_id,
      timestamp: item.created_at,
      payload: item.payload,
    })),
  };
}

export async function fetchAuditLog(
  options: CorpusClientOptions,
  params?: {
    event_type?: string;
    entity_id?: string;
    entity_type?: string;
    page?: number;
  },
): Promise<AuditPage> {
  const url = new URL(`${options.baseUrl}/internal/v1/audit`);
  if (params?.event_type) url.searchParams.set("event_type", params.event_type);
  if (params?.entity_id) url.searchParams.set("entity_id", params.entity_id);
  if (params?.entity_type) {
    url.searchParams.set("entity_type", params.entity_type);
  }
  if (params?.page) url.searchParams.set("page", String(params.page));
  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok)
    throw new Error(`Audit log failed (${String(response.status)})`);
  const raw = (await response.json()) as AuditLogResponseApi;
  return parseAuditLogResponse(raw);
}

export async function fetchDocumentHistory(
  options: CorpusClientOptions,
  documentId: string,
): Promise<AuditEvent[]> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/audit?entity_id=${documentId}`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      },
    },
  );
  if (!response.ok)
    throw new Error(`Document history failed (${String(response.status)})`);
  const raw = (await response.json()) as AuditLogResponseApi;
  return parseAuditLogResponse(raw).events;
}

export async function bulkUpdateMetadata(
  options: CorpusClientOptions,
  documentIds: string[],
  updates: { title?: string; language?: string },
): Promise<BulkResult> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/bulk/metadata`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ document_ids: documentIds, ...updates }),
    },
  );
  if (!response.ok)
    throw new Error(`Bulk metadata update failed (${String(response.status)})`);
  return response.json() as Promise<BulkResult>;
}

export interface EvalMetricsSummaryApi {
  retrieval_relevance?: number | null;
  faithfulness?: number | null;
  answer_relevancy?: number | null;
  latency_p95_ms?: number | null;
  custom_scores?: Record<string, number> | null;
}

export interface EvalRunListItemApi {
  run_id: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at?: string | null;
  completed_at?: string | null;
  metrics_summary: EvalMetricsSummaryApi;
  error_message?: string | null;
}

export interface EvalRunListResponseApi {
  items: EvalRunListItemApi[];
  page: number;
  page_size: number;
  total_count: number;
}

export interface EvalRunItemApi {
  case_id: string;
  locale: string;
  question: string;
  expected_doc_url?: string | null;
  retrieved_urls: string[];
  answer?: string | null;
  metrics: {
    retrieval_pass: boolean;
    faithfulness?: number | null;
    answer_relevancy?: number | null;
    latency_ms: number;
    custom_scores?: Record<string, number> | null;
  };
}

export interface EvalRunDetailApi {
  run_id: string;
  status: "pending" | "running" | "completed" | "failed";
  metrics_summary: EvalMetricsSummaryApi;
  items: EvalRunItemApi[];
  error_message?: string | null;
}

export async function fetchEvalRuns(
  options: CorpusClientOptions,
): Promise<EvalRunListResponseApi> {
  const response = await fetch(`${options.baseUrl}/internal/v1/eval/runs`, {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Eval runs list failed (${String(response.status)})`);
  }
  return response.json() as Promise<EvalRunListResponseApi>;
}

export async function fetchEvalRunDetail(
  options: CorpusClientOptions,
  runId: string,
): Promise<EvalRunDetailApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/runs/${runId}`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Eval run detail failed (${String(response.status)})`);
  }
  return response.json() as Promise<EvalRunDetailApi>;
}

export async function triggerEvalRun(
  options: CorpusClientOptions,
  corpusProfile: "fixture" | "staging" = "fixture",
): Promise<{ run_id: string; status: string; created_at: string }> {
  const response = await fetch(`${options.baseUrl}/internal/v1/eval/runs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ corpus_profile: corpusProfile }),
  });
  if (!response.ok) {
    throw new Error(`Eval run trigger failed (${String(response.status)})`);
  }
  return response.json() as Promise<{
    run_id: string;
    status: string;
    created_at: string;
  }>;
}

export type EvalRunModeApi = "golden" | "adhoc";

export interface EvalConfigPartialApi {
  top_k?: number;
  min_retrieval_score?: number;
  system_prompt?: string;
  max_tokens?: number;
  temperature?: number;
  corpus_profile?: "fixture" | "staging";
  judge_temperature?: number;
  model_id?: string;
}

export interface EvalConfigApi {
  top_k: number;
  min_retrieval_score: number;
  system_prompt: string;
  max_tokens: number;
  temperature: number;
  corpus_profile: "fixture" | "staging";
  criteria_ids: string[];
  judge_temperature: number;
  model_id: string;
}

export interface EvalConfigPresetApi {
  preset_id: string;
  version: number;
  name: string;
  config: EvalConfigApi;
  shared: boolean;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface EvalConfigPresetCreateRequestApi {
  name: string;
  config: EvalConfigApi;
  shared?: boolean;
}

export interface EvalConfigPresetUpdateRequestApi {
  name?: string;
  config?: EvalConfigApi;
  shared?: boolean;
}

export async function fetchEvalConfigPresets(
  options: CorpusClientOptions,
): Promise<{ items: EvalConfigPresetApi[] }> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/config-presets`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      },
    },
  );
  if (!response.ok) {
    throw new Error(
      `Eval config presets list failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<{ items: EvalConfigPresetApi[] }>;
}

export async function createEvalConfigPreset(
  options: CorpusClientOptions,
  body: EvalConfigPresetCreateRequestApi,
): Promise<EvalConfigPresetApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/config-presets`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Eval config preset create failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EvalConfigPresetApi>;
}

export async function updateEvalConfigPreset(
  options: CorpusClientOptions,
  presetId: string,
  body: EvalConfigPresetUpdateRequestApi,
): Promise<EvalConfigPresetApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/config-presets/${presetId}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Eval config preset update failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EvalConfigPresetApi>;
}

export async function cloneEvalConfigPreset(
  options: CorpusClientOptions,
  presetId: string,
  name?: string,
): Promise<EvalConfigPresetApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/config-presets/${presetId}/clone`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(name ? { name } : {}),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Eval config preset clone failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EvalConfigPresetApi>;
}

export interface RagConfigPromoteRequestApi {
  source: "preset" | "run";
  preset_id?: string;
  run_id?: string;
}

export interface RagConfigPromoteResponseApi {
  config_version: number;
  promoted_at: string;
  promoted_by: string;
}

export interface RagConfigActiveResponseApi {
  config: EvalConfigApi;
  config_version: number;
  promoted_at?: string | null;
  promoted_by?: string | null;
}

export async function promoteRagConfig(
  options: CorpusClientOptions,
  body: RagConfigPromoteRequestApi,
): Promise<RagConfigPromoteResponseApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/rag/config/promote`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(`RAG config promote failed (${String(response.status)})`);
  }
  return response.json() as Promise<RagConfigPromoteResponseApi>;
}

export async function fetchActiveRagConfig(
  options: CorpusClientOptions,
): Promise<RagConfigActiveResponseApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/rag/config/active`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      },
    },
  );
  if (!response.ok) {
    throw new Error(
      `Active RAG config fetch failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<RagConfigActiveResponseApi>;
}

export interface PlaygroundEvalRunRequestApi {
  mode: EvalRunModeApi;
  question?: string;
  config?: EvalConfigPartialApi;
  preset_id?: string | null;
}

export async function triggerPlaygroundEvalRun(
  options: CorpusClientOptions,
  body: PlaygroundEvalRunRequestApi,
): Promise<{ run_id: string; status: string; created_at: string }> {
  const response = await fetch(`${options.baseUrl}/internal/v1/eval/runs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Eval run trigger failed (${String(response.status)})`);
  }
  return response.json() as Promise<{
    run_id: string;
    status: string;
    created_at: string;
  }>;
}

export interface OllamaModelSummaryApi {
  model_id: string;
  available: boolean;
}

export async function fetchOllamaModels(
  options: CorpusClientOptions,
): Promise<{ items: OllamaModelSummaryApi[] }> {
  const response = await fetch(`${options.baseUrl}/internal/v1/models/ollama`, {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Ollama models list failed (${String(response.status)})`);
  }
  return response.json() as Promise<{ items: OllamaModelSummaryApi[] }>;
}

export interface OllamaModelPullResponseApi {
  job_id: string;
  model_id: string;
  status: "pulling" | "available";
}

export async function pullOllamaModel(
  options: CorpusClientOptions,
  modelId: string,
): Promise<OllamaModelPullResponseApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/models/ollama/pull`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model_id: modelId }),
    },
  );
  if (!response.ok) {
    throw new Error(`Ollama model pull failed (${String(response.status)})`);
  }
  return response.json() as Promise<OllamaModelPullResponseApi>;
}

export interface EvalTimeseriesPointApi {
  run_id: string;
  completed_at: string;
  metrics_summary: EvalMetricsSummaryApi;
}

export interface EvalTimeseriesResponseApi {
  points: EvalTimeseriesPointApi[];
  available_metrics: string[];
}

export async function fetchEvalTimeseries(
  options: CorpusClientOptions,
  limit = 100,
): Promise<EvalTimeseriesResponseApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/runs/timeseries?limit=${String(limit)}`,
    {
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Eval timeseries failed (${String(response.status)})`);
  }
  return response.json() as Promise<EvalTimeseriesResponseApi>;
}

export interface EvalCriterionApi {
  criterion_id: string;
  slug: string;
  label: string;
  description?: string | null;
  scorer_type: "llm_rubric";
  rubric: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchEvalCriteria(
  options: CorpusClientOptions,
): Promise<{ items: EvalCriterionApi[] }> {
  const response = await fetch(`${options.baseUrl}/internal/v1/eval/criteria`, {
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Eval criteria list failed (${String(response.status)})`);
  }
  return response.json() as Promise<{ items: EvalCriterionApi[] }>;
}

export async function createEvalCriterion(
  options: CorpusClientOptions,
  body: {
    slug: string;
    label: string;
    description?: string | null;
    rubric: string;
    enabled?: boolean;
  },
): Promise<EvalCriterionApi> {
  const response = await fetch(`${options.baseUrl}/internal/v1/eval/criteria`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scorer_type: "llm_rubric",
      enabled: body.enabled ?? true,
      ...body,
    }),
  });
  if (!response.ok) {
    throw new Error(
      `Eval criterion create failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EvalCriterionApi>;
}

export async function updateEvalCriterion(
  options: CorpusClientOptions,
  criterionId: string,
  body: {
    label?: string;
    description?: string | null;
    rubric?: string;
    enabled?: boolean;
  },
): Promise<EvalCriterionApi> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/eval/criteria/${criterionId}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${options.accessToken ?? options.apiKey ?? ""}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Eval criterion update failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EvalCriterionApi>;
}
