import type { TagInput } from "./types";
import type { CorpusClientOptions } from "./corpus";

export interface StatsSummary {
  total_documents: number;
  total_chunks: number;
  tag_distribution: { tag: string; count: number }[];
  language_breakdown: { language: string; count: number }[];
  recent_activity: { event_type: string; entity_type: string; entity_id: string; timestamp: string }[];
  top_served: { document_id: string; title: string | null; served_count: number }[];
}

export interface ServiceHealth {
  name: string;
  status: "healthy" | "unhealthy";
  latency_ms: number | null;
  error: string | null;
}

export interface HealthAggregate {
  overall: "healthy" | "degraded";
  services: ServiceHealth[];
  checked_at: string;
}

export async function fetchStatsSummary(options: CorpusClientOptions): Promise<StatsSummary> {
  const response = await fetch(`${options.baseUrl}/internal/v1/stats/summary`, {
    headers: { Authorization: `Bearer ${options.apiKey}` },
  });
  if (!response.ok) {
    throw new Error(`Stats summary failed (${response.status})`);
  }
  return response.json() as Promise<StatsSummary>;
}

export async function fetchHealthAggregate(options: CorpusClientOptions): Promise<HealthAggregate> {
  const response = await fetch(`${options.baseUrl}/internal/v1/health/all`, {
    headers: { Authorization: `Bearer ${options.apiKey}` },
  });
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return response.json() as Promise<HealthAggregate>;
}

export interface BulkResult {
  successes: string[];
  failures: { document_id: string; error: string }[];
}

export async function bulkDeleteDocuments(
  options: CorpusClientOptions,
  documentIds: string[],
): Promise<BulkResult> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/bulk`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${options.apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  });
  if (!response.ok) throw new Error(`Bulk delete failed (${response.status})`);
  return response.json() as Promise<BulkResult>;
}

export async function bulkTagDocuments(
  options: CorpusClientOptions,
  documentIds: string[],
  addTags: TagInput[],
  removeSlugs: string[],
): Promise<BulkResult> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/bulk/tags`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${options.apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds, add: addTags, remove: removeSlugs }),
  });
  if (!response.ok) throw new Error(`Bulk tag failed (${response.status})`);
  return response.json() as Promise<BulkResult>;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface AuditPage {
  events: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
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
  if (!response.ok) throw new Error(`Audit log failed (${response.status})`);
  return response.json() as Promise<AuditPage>;
}

export async function fetchDocumentHistory(
  options: CorpusClientOptions,
  documentId: string,
): Promise<AuditEvent[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/audit?entity_id=${documentId}`, {
    headers: { Authorization: `Bearer ${options.apiKey}` },
  });
  if (!response.ok) throw new Error(`Document history failed (${response.status})`);
  const body = (await response.json()) as { events: AuditEvent[] };
  return body.events;
}

export async function bulkUpdateMetadata(
  options: CorpusClientOptions,
  documentIds: string[],
  updates: { title?: string; language?: string },
): Promise<BulkResult> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/bulk/metadata`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${options.apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds, ...updates }),
  });
  if (!response.ok) throw new Error(`Bulk metadata update failed (${response.status})`);
  return response.json() as Promise<BulkResult>;
}
