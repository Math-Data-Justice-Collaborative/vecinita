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
