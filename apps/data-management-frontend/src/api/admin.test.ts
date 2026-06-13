import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody, mockFetchUrl } from "@/test/fetch-mock";

import {
  bulkDeleteDocuments,
  bulkTagDocuments,
  bulkUpdateMetadata,
  fetchAuditLog,
  fetchDocumentHistory,
  fetchHealthAggregate,
  fetchStatsSummary,
  parseAuditLogResponse,
  parseHealthAggregate,
  parseStatsSummary,
} from "./admin";

const CLIENT = { baseUrl: "http://localhost:8002", apiKey: "test-key" };

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("admin API parsers", () => {
  it("parseStatsSummary normalizes wire format", () => {
    const parsed = parseStatsSummary({
      total_documents: 2,
      total_chunks: 10,
      tag_distribution: [
        { slug: "a", label: "Alpha", document_count: 1 },
        { slug: "b", label: "", document_count: 2 },
      ],
      language_breakdown: { en: 1, es: 1 },
      recent_activity: [
        {
          event_type: "document.created",
          entity_id: "d1",
          created_at: "2026-01-01T00:00:00Z",
          summary: "Created",
        },
        {
          event_type: "no_dot_event",
          entity_id: "d2",
          created_at: "2026-01-02T00:00:00Z",
          summary: null,
        },
      ],
      top_served: [{ document_id: "d1", title: "Doc", served_count: 5 }],
    });

    expect(parsed.tag_distribution[0]).toEqual({ tag: "Alpha", count: 1 });
    expect(parsed.tag_distribution[1]).toEqual({ tag: "b", count: 2 });
    expect(parsed.recent_activity[0]?.entity_type).toBe("document");
    expect(parsed.recent_activity[1]?.entity_type).toBe("no_dot_event");
    expect(parsed.recent_activity[1]?.summary).toBeNull();
  });

  it("parseHealthAggregate maps up/down to healthy/unhealthy", () => {
    const parsed = parseHealthAggregate({
      status: "degraded",
      checked_at: "2026-01-01T00:00:00Z",
      services: {
        api: { status: "up", latency_ms: 12, error: null },
        worker: { status: "down", latency_ms: null, error: "timeout" },
      },
    });

    expect(parsed.overall).toBe("degraded");
    expect(parsed.services[0]?.status).toBe("healthy");
    expect(parsed.services[1]?.status).toBe("unhealthy");
    expect(parsed.services[1]?.error).toBe("timeout");
  });

  it("parseAuditLogResponse maps items to events", () => {
    const parsed = parseAuditLogResponse({
      items: [
        {
          id: "e1",
          event_type: "document.created",
          entity_type: "document",
          entity_id: "d1",
          request_id: "r1",
          payload: { x: 1 },
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      page: 2,
      page_size: 25,
      total_count: 100,
    });

    expect(parsed.total).toBe(100);
    expect(parsed.events[0]?.timestamp).toBe("2026-01-01T00:00:00Z");
  });
});

describe("admin API fetch helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchStatsSummary fetches and parses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          total_documents: 0,
          total_chunks: 0,
          tag_distribution: [],
          language_breakdown: {},
          recent_activity: [],
          top_served: [],
        }),
      ),
    );
    const stats = await fetchStatsSummary(CLIENT);
    expect(stats.total_documents).toBe(0);
  });

  it("fetchStatsSummary throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchStatsSummary(CLIENT)).rejects.toThrow(/500/);
  });

  it("fetchHealthAggregate fetches and parses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          status: "healthy",
          checked_at: "2026-01-01T00:00:00Z",
          services: {},
        }),
      ),
    );
    const health = await fetchHealthAggregate(CLIENT);
    expect(health.overall).toBe("healthy");
  });

  it("fetchHealthAggregate throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 503 })),
    );
    await expect(fetchHealthAggregate(CLIENT)).rejects.toThrow(/503/);
  });

  it("bulkDeleteDocuments sends document_ids", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ successes: ["d1"], failures: [] })),
    );
    const result = await bulkDeleteDocuments(CLIENT, ["d1"]);
    expect(result.successes).toEqual(["d1"]);
  });

  it("bulkDeleteDocuments throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 400 })),
    );
    await expect(bulkDeleteDocuments(CLIENT, [])).rejects.toThrow(/400/);
  });

  it("bulkTagDocuments sends add/remove tags", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ successes: ["d1"], failures: [] })),
    );
    const tags = [{ slug: "a", label: "A", source: "human" as const }];
    await bulkTagDocuments(CLIENT, ["d1"], tags, ["old"]);
    const body = mockFetchJsonBody();
    expect(body["add"]).toEqual(tags);
    expect(body["remove"]).toEqual(["old"]);
  });

  it("bulkTagDocuments throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 409 })),
    );
    await expect(bulkTagDocuments(CLIENT, [], [], [])).rejects.toThrow(/409/);
  });

  it("bulkUpdateMetadata sends optional fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ successes: ["d1"], failures: [] })),
    );
    await bulkUpdateMetadata(CLIENT, ["d1"], { title: "New", language: "es" });
    const body = mockFetchJsonBody();
    expect(body["title"]).toBe("New");
    expect(body["language"]).toBe("es");
  });

  it("bulkUpdateMetadata throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 422 })),
    );
    await expect(bulkUpdateMetadata(CLIENT, [], {})).rejects.toThrow(/422/);
  });

  it("fetchAuditLog builds query params", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [],
          page: 1,
          page_size: 50,
          total_count: 0,
        }),
      ),
    );
    await fetchAuditLog(CLIENT, {
      event_type: "document.created",
      entity_id: "d1",
      page: 2,
    });
    const url = mockFetchUrl();
    expect(url).toContain("event_type=document.created");
    expect(url).toContain("entity_id=d1");
    expect(url).toContain("page=2");
  });

  it("fetchAuditLog throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchAuditLog(CLIENT)).rejects.toThrow(/500/);
  });

  it("fetchDocumentHistory returns events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [
            {
              id: "e1",
              event_type: "document.created",
              entity_type: "document",
              entity_id: "d1",
              request_id: "r1",
              payload: {},
              created_at: "2026-01-01T00:00:00Z",
            },
          ],
          page: 1,
          page_size: 50,
          total_count: 1,
        }),
      ),
    );
    const events = await fetchDocumentHistory(CLIENT, "d1");
    expect(events).toHaveLength(1);
  });

  it("fetchDocumentHistory throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(fetchDocumentHistory(CLIENT, "d1")).rejects.toThrow(/404/);
  });
});
