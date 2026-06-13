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
    headers: { Authorization: `Bearer ${options.apiKey}` },
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
    headers: { Authorization: `Bearer ${options.apiKey}` },
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
        Authorization: `Bearer ${options.apiKey}`,
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
        Authorization: `Bearer ${options.apiKey}`,
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
  params?: { event_type?: string; entity_id?: string; page?: number },
): Promise<AuditPage> {
  const url = new URL(`${options.baseUrl}/internal/v1/audit`);
  if (params?.event_type) url.searchParams.set("event_type", params.event_type);
  if (params?.entity_id) url.searchParams.set("entity_id", params.entity_id);
  if (params?.page) url.searchParams.set("page", String(params.page));
  const response = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${options.apiKey}` },
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
      headers: { Authorization: `Bearer ${options.apiKey}` },
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
        Authorization: `Bearer ${options.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ document_ids: documentIds, ...updates }),
    },
  );
  if (!response.ok)
    throw new Error(`Bulk metadata update failed (${String(response.status)})`);
  return response.json() as Promise<BulkResult>;
}
