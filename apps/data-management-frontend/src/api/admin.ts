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
