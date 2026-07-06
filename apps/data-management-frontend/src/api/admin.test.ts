import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody, mockFetchUrl } from "@/test/fetch-mock";

import {
  bulkDeleteDocuments,
  bulkTagDocuments,
  bulkUpdateMetadata,
  cloneEvalConfigPreset,
  createEvalConfigPreset,
  createEvalCriterion,
  fetchAuditLog,
  fetchDocumentHistory,
  fetchActiveRagConfig,
  fetchEvalConfigPresets,
  fetchEvalCriteria,
  fetchEvalRunDetail,
  fetchEvalRuns,
  fetchEvalTimeseries,
  fetchHealthAggregate,
  fetchOllamaModels,
  fetchStatsSummary,
  parseAuditLogResponse,
  parseHealthAggregate,
  parseStatsSummary,
  promoteRagConfig,
  pullOllamaModel,
  triggerEvalRun,
  triggerPlaygroundEvalRun,
  updateEvalConfigPreset,
  updateEvalCriterion,
} from "./admin";

const CLIENT = { baseUrl: "http://localhost:8002", apiKey: "test-key" };
const JWT_CLIENT = {
  baseUrl: "http://localhost:8002",
  accessToken: "jwt-token",
};

function expectBearerJwt(init: RequestInit | undefined): void {
  const headers = init?.headers as Record<string, string> | undefined;
  expect(headers?.["Authorization"]).toBe("Bearer jwt-token");
}

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

  it("fetch helpers prefer accessToken over apiKey (F34)", async () => {
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
    await fetchStatsSummary(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[0]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        status: "healthy",
        checked_at: "2026-01-01T00:00:00Z",
        services: {},
      }),
    );
    await fetchHealthAggregate(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[1]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ successes: ["d1"], failures: [] }),
    );
    await bulkDeleteDocuments(JWT_CLIENT, ["d1"]);
    expectBearerJwt(vi.mocked(fetch).mock.calls[2]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        items: [],
        page: 1,
        page_size: 50,
        total_count: 0,
      }),
    );
    await fetchAuditLog(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[3]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        items: [],
        page: 1,
        page_size: 50,
        total_count: 0,
      }),
    );
    await fetchDocumentHistory(JWT_CLIENT, "d1");
    expectBearerJwt(vi.mocked(fetch).mock.calls[4]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ successes: ["d1"], failures: [] }),
    );
    await bulkTagDocuments(JWT_CLIENT, ["d1"], [], []);
    expectBearerJwt(vi.mocked(fetch).mock.calls[5]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ successes: ["d1"], failures: [] }),
    );
    await bulkUpdateMetadata(JWT_CLIENT, ["d1"], { title: "T" });
    expectBearerJwt(vi.mocked(fetch).mock.calls[6]?.[1]);
  });

  it("fetch helpers send empty bearer when no token or api key", async () => {
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
    await fetchStatsSummary({ baseUrl: CLIENT.baseUrl });
    const headers = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBe("Bearer ");
  });

  it("bulkTagDocuments and bulkUpdateMetadata use JWT bearer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ successes: [], failures: [] })),
    );
    await bulkTagDocuments(JWT_CLIENT, [], [], []);
    const tagHeaders = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(tagHeaders["Authorization"]).toBe("Bearer jwt-token");

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ successes: [], failures: [] }),
    );
    await bulkUpdateMetadata(JWT_CLIENT, [], {});
    const metaHeaders = vi.mocked(fetch).mock.calls[1]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(metaHeaders["Authorization"]).toBe("Bearer jwt-token");
  });

  it("remaining fetch helpers tolerate missing bearer", async () => {
    const bare = { baseUrl: CLIENT.baseUrl };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/health/all")) {
          return Promise.resolve(
            jsonResponse({
              status: "healthy",
              checked_at: "2026-01-01T00:00:00Z",
              services: {},
            }),
          );
        }
        if (url.includes("/audit")) {
          return Promise.resolve(
            jsonResponse({
              items: [],
              page: 1,
              page_size: 50,
              total_count: 0,
            }),
          );
        }
        if (url.includes("/history")) {
          return Promise.resolve(
            jsonResponse({
              items: [],
              page: 1,
              page_size: 50,
              total_count: 0,
            }),
          );
        }
        return Promise.resolve(jsonResponse({ successes: [], failures: [] }));
      }),
    );
    await fetchHealthAggregate(bare);
    await fetchAuditLog(bare);
    await fetchDocumentHistory(bare, "d1");
    await bulkDeleteDocuments(bare, []);
    await bulkTagDocuments(bare, [], [], []);
    await bulkUpdateMetadata(bare, [], {});
  });
});

const EVAL_CONFIG = {
  top_k: 5,
  min_retrieval_score: 0.2,
  system_prompt: "Test prompt",
  max_tokens: 256,
  temperature: 0.2,
  corpus_profile: "fixture" as const,
  criteria_ids: [] as string[],
  judge_temperature: 0.2,
  model_id: "qwen2.5:1.5b-instruct",
};

const EVAL_PRESET = {
  preset_id: "00000000-0000-0000-0000-0000000000aa",
  version: 1,
  name: "baseline",
  config: EVAL_CONFIG,
  shared: false,
  owner_id: "11111111-1111-1111-1111-111111111111",
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-01T10:00:00Z",
};

const EVAL_CRITERION = {
  criterion_id: "00000000-0000-0000-0000-000000000077",
  slug: "tone-friendly",
  label: "Friendly tone",
  rubric: "Supportive tone",
  scorer_type: "llm_rubric" as const,
  enabled: true,
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-01T10:00:00Z",
};

describe("admin API eval helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchEvalRuns fetches list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [],
          page: 1,
          page_size: 20,
          total_count: 0,
        }),
      ),
    );
    const runs = await fetchEvalRuns(CLIENT);
    expect(runs.total_count).toBe(0);
  });

  it("fetchEvalRuns throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 503 })),
    );
    await expect(fetchEvalRuns(CLIENT)).rejects.toThrow(/503/);
  });

  it("fetchEvalRunDetail fetches detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          run_id: "00000000-0000-0000-0000-000000000099",
          status: "completed",
          metrics_summary: {},
          items: [],
        }),
      ),
    );
    const detail = await fetchEvalRunDetail(
      CLIENT,
      "00000000-0000-0000-0000-000000000099",
    );
    expect(detail.status).toBe("completed");
  });

  it("fetchEvalRunDetail throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(fetchEvalRunDetail(CLIENT, "missing")).rejects.toThrow(/404/);
  });

  it("triggerEvalRun posts corpus profile", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          run_id: "00000000-0000-0000-0000-000000000099",
          status: "pending",
          created_at: "2026-07-01T12:00:00Z",
        }),
      ),
    );
    const created = await triggerEvalRun(CLIENT, "staging");
    expect(created.status).toBe("pending");
    const body = mockFetchJsonBody();
    expect(body["corpus_profile"]).toBe("staging");
  });

  it("triggerEvalRun throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(triggerEvalRun(CLIENT)).rejects.toThrow(/500/);
  });

  it("fetchEvalConfigPresets fetches presets", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ items: [EVAL_PRESET] })),
    );
    const presets = await fetchEvalConfigPresets(CLIENT);
    expect(presets.items[0]?.name).toBe("baseline");
  });

  it("fetchEvalConfigPresets throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchEvalConfigPresets(CLIENT)).rejects.toThrow(/500/);
  });

  it("createEvalConfigPreset posts body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(EVAL_PRESET)),
    );
    const created = await createEvalConfigPreset(CLIENT, {
      name: "baseline",
      config: EVAL_CONFIG,
      shared: true,
    });
    expect(created.preset_id).toBe(EVAL_PRESET.preset_id);
  });

  it("createEvalConfigPreset throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 422 })),
    );
    await expect(
      createEvalConfigPreset(CLIENT, {
        name: "baseline",
        config: EVAL_CONFIG,
      }),
    ).rejects.toThrow(/422/);
  });

  it("updateEvalConfigPreset patches preset", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ ...EVAL_PRESET, version: 2, name: "baseline-v2" }),
        ),
    );
    const updated = await updateEvalConfigPreset(
      CLIENT,
      EVAL_PRESET.preset_id,
      {
        name: "baseline-v2",
      },
    );
    expect(updated.version).toBe(2);
  });

  it("updateEvalConfigPreset throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(
      updateEvalConfigPreset(CLIENT, EVAL_PRESET.preset_id, { name: "x" }),
    ).rejects.toThrow(/403/);
  });

  it("cloneEvalConfigPreset posts optional name", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          ...EVAL_PRESET,
          preset_id: "00000000-0000-0000-0000-0000000000bb",
        }),
      ),
    );
    await cloneEvalConfigPreset(CLIENT, EVAL_PRESET.preset_id, "copy");
    const body = mockFetchJsonBody();
    expect(body["name"]).toBe("copy");
  });

  it("cloneEvalConfigPreset posts empty body when name omitted", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          ...EVAL_PRESET,
          preset_id: "00000000-0000-0000-0000-0000000000cc",
        }),
      ),
    );
    await cloneEvalConfigPreset(CLIENT, EVAL_PRESET.preset_id);
    expect(mockFetchJsonBody()).toEqual({});
  });

  it("cloneEvalConfigPreset throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 409 })),
    );
    await expect(
      cloneEvalConfigPreset(CLIENT, EVAL_PRESET.preset_id),
    ).rejects.toThrow(/409/);
  });

  it("promoteRagConfig posts preset source body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          config_version: 2,
          promoted_at: "2026-07-02T12:00:00Z",
          promoted_by: "44444444-4444-4444-4444-444444444444",
        }),
      ),
    );
    await promoteRagConfig(JWT_CLIENT, {
      source: "preset",
      preset_id: EVAL_PRESET.preset_id,
    });
    expect(mockFetchUrl()).toContain("/internal/v1/rag/config/promote");
    expect(mockFetchJsonBody()).toEqual({
      source: "preset",
      preset_id: EVAL_PRESET.preset_id,
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[0]?.[1]);
  });

  it("promoteRagConfig throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(
      promoteRagConfig(JWT_CLIENT, {
        source: "preset",
        preset_id: EVAL_PRESET.preset_id,
      }),
    ).rejects.toThrow(/403/);
  });

  it("fetchActiveRagConfig reads active production config", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          config: EVAL_PRESET.config,
          config_version: 1,
          promoted_at: "2026-07-02T12:00:00Z",
          promoted_by: "44444444-4444-4444-4444-444444444444",
        }),
      ),
    );
    const active = await fetchActiveRagConfig(JWT_CLIENT);
    expect(active.config_version).toBe(1);
    expect(mockFetchUrl()).toContain("/internal/v1/rag/config/active");
  });

  it("fetchActiveRagConfig throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(fetchActiveRagConfig(JWT_CLIENT)).rejects.toThrow(/404/);
  });

  it("triggerPlaygroundEvalRun posts playground body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          run_id: "00000000-0000-0000-0000-000000000099",
          status: "pending",
          created_at: "2026-07-01T12:00:00Z",
        }),
      ),
    );
    await triggerPlaygroundEvalRun(CLIENT, {
      mode: "adhoc",
      question: "Test?",
      config: { top_k: 3 },
      preset_id: EVAL_PRESET.preset_id,
    });
    const body = mockFetchJsonBody();
    expect(body["mode"]).toBe("adhoc");
    expect(body["question"]).toBe("Test?");
  });

  it("triggerPlaygroundEvalRun throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(
      triggerPlaygroundEvalRun(CLIENT, { mode: "golden" }),
    ).rejects.toThrow(/500/);
  });

  it("fetchOllamaModels fetches models", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [{ model_id: "qwen2.5:1.5b-instruct", available: true }],
        }),
      ),
    );
    const models = await fetchOllamaModels(CLIENT);
    expect(models.items[0]?.model_id).toContain("qwen");
  });

  it("fetchOllamaModels throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 502 })),
    );
    await expect(fetchOllamaModels(CLIENT)).rejects.toThrow(/502/);
  });

  it("pullOllamaModel POSTs pull route with model_id (TC-135)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            job_id: "00000000-0000-0000-0000-0000000000dd",
            model_id: "qwen2.5:3b-instruct",
            status: "pulling",
          },
          202,
        ),
      ),
    );
    const result = await pullOllamaModel(JWT_CLIENT, "qwen2.5:3b-instruct");
    expect(result.status).toBe("pulling");
    expect(mockFetchUrl()).toContain("/internal/v1/models/ollama/pull");
    expect(mockFetchJsonBody()).toEqual({ model_id: "qwen2.5:3b-instruct" });
    expectBearerJwt(vi.mocked(fetch).mock.calls[0]?.[1]);
  });

  it("pullOllamaModel throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(
      pullOllamaModel(JWT_CLIENT, "qwen2.5:3b-instruct"),
    ).rejects.toThrow(/403/);
  });

  it("pullOllamaModel uses apiKey when accessToken is absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            job_id: "00000000-0000-0000-0000-0000000000dd",
            model_id: "qwen2.5:3b-instruct",
            status: "pulling",
          },
          202,
        ),
      ),
    );
    await pullOllamaModel(CLIENT, "qwen2.5:3b-instruct");
    const headers = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBe("Bearer test-key");
  });

  it("pullOllamaModel sends empty bearer when auth options are absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            job_id: "00000000-0000-0000-0000-0000000000dd",
            model_id: "qwen2.5:3b-instruct",
            status: "pulling",
          },
          202,
        ),
      ),
    );
    await pullOllamaModel({ baseUrl: "http://localhost:8002" }, "qwen2.5:3b-instruct");
    const headers = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBe("Bearer ");
  });

  it("fetchEvalTimeseries fetches with limit", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ points: [], available_metrics: [] })),
    );
    await fetchEvalTimeseries(CLIENT, 50);
    const url = mockFetchUrl();
    expect(url).toContain("limit=50");
  });

  it("fetchEvalTimeseries throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchEvalTimeseries(CLIENT)).rejects.toThrow(/500/);
  });

  it("fetchEvalCriteria fetches criteria", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ items: [EVAL_CRITERION] })),
    );
    const criteria = await fetchEvalCriteria(CLIENT);
    expect(criteria.items[0]?.slug).toBe("tone-friendly");
  });

  it("fetchEvalCriteria throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchEvalCriteria(CLIENT)).rejects.toThrow(/500/);
  });

  it("createEvalCriterion posts criterion", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(EVAL_CRITERION)),
    );
    const created = await createEvalCriterion(CLIENT, {
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
      enabled: false,
    });
    expect(created.enabled).toBe(true);
    const body = mockFetchJsonBody();
    expect(body["scorer_type"]).toBe("llm_rubric");
  });

  it("createEvalCriterion throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 400 })),
    );
    await expect(
      createEvalCriterion(CLIENT, {
        slug: "x",
        label: "X",
        rubric: "R",
      }),
    ).rejects.toThrow(/400/);
  });

  it("updateEvalCriterion patches criterion", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ ...EVAL_CRITERION, enabled: false })),
    );
    const updated = await updateEvalCriterion(
      CLIENT,
      EVAL_CRITERION.criterion_id,
      { enabled: false },
    );
    expect(updated.enabled).toBe(false);
  });

  it("updateEvalCriterion throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(
      updateEvalCriterion(CLIENT, EVAL_CRITERION.criterion_id, {
        label: "New",
      }),
    ).rejects.toThrow(/404/);
  });

  it("triggerEvalRun defaults corpus profile to fixture", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          run_id: "00000000-0000-0000-0000-000000000099",
          status: "pending",
          created_at: "2026-07-01T12:00:00Z",
        }),
      ),
    );
    await triggerEvalRun(CLIENT);
    expect(mockFetchJsonBody()["corpus_profile"]).toBe("fixture");
  });

  it("createEvalCriterion defaults enabled to true when omitted", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(EVAL_CRITERION)),
    );
    await createEvalCriterion(CLIENT, {
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
    });
    expect(mockFetchJsonBody()["enabled"]).toBe(true);
  });

  it("eval fetch helpers send empty bearer when no token or api key", async () => {
    const bare = { baseUrl: CLIENT.baseUrl };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/eval/config-presets") && !url.includes("/clone")) {
          if (url.endsWith("/eval/config-presets")) {
            return Promise.resolve(jsonResponse({ items: [] }));
          }
          return Promise.resolve(jsonResponse(EVAL_PRESET));
        }
        if (url.includes("/clone")) {
          return Promise.resolve(jsonResponse(EVAL_PRESET));
        }
        if (url.includes("/models/ollama")) {
          return Promise.resolve(jsonResponse({ items: [] }));
        }
        if (url.includes("/eval/runs") && url.includes("timeseries")) {
          return Promise.resolve(
            jsonResponse({ points: [], available_metrics: [] }),
          );
        }
        if (url.includes("/eval/runs/")) {
          return Promise.resolve(
            jsonResponse({
              run_id: "00000000-0000-0000-0000-000000000099",
              status: "completed",
              metrics_summary: {},
              items: [],
            }),
          );
        }
        if (url.includes("/eval/runs")) {
          return Promise.resolve(
            jsonResponse({
              run_id: "00000000-0000-0000-0000-000000000099",
              status: "pending",
              created_at: "2026-07-01T12:00:00Z",
            }),
          );
        }
        if (url.includes("/eval/criteria")) {
          return Promise.resolve(jsonResponse({ items: [EVAL_CRITERION] }));
        }
        if (url.includes("/rag/config/promote")) {
          return Promise.resolve(
            jsonResponse({
              config_version: 1,
              promoted_at: "2026-07-02T12:00:00Z",
              promoted_by: "44444444-4444-4444-4444-444444444444",
            }),
          );
        }
        if (url.includes("/rag/config/active")) {
          return Promise.resolve(
            jsonResponse({
              config: EVAL_PRESET.config,
              config_version: 1,
            }),
          );
        }
        return Promise.resolve(jsonResponse({ items: [] }));
      }),
    );

    await fetchEvalConfigPresets(bare);
    await createEvalConfigPreset(bare, { name: "x", config: EVAL_CONFIG });
    await updateEvalConfigPreset(bare, EVAL_PRESET.preset_id, { name: "y" });
    await cloneEvalConfigPreset(bare, EVAL_PRESET.preset_id);
    await triggerPlaygroundEvalRun(bare, { mode: "golden" });
    await promoteRagConfig(bare, {
      source: "preset",
      preset_id: EVAL_PRESET.preset_id,
    });
    await fetchActiveRagConfig(bare);
    await fetchOllamaModels(bare);
    await fetchEvalTimeseries(bare);
    await fetchEvalRunDetail(bare, "00000000-0000-0000-0000-000000000099");
    await fetchEvalRuns(bare);
    await triggerEvalRun(bare);
    await fetchEvalCriteria(bare);
    await createEvalCriterion(bare, {
      slug: "x",
      label: "X",
      rubric: "R",
    });
    await updateEvalCriterion(bare, EVAL_CRITERION.criterion_id, {
      label: "Y",
    });

    const headers = vi.mocked(fetch).mock.calls.at(-1)?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBe("Bearer ");
  });

  it("eval fetch helpers prefer accessToken over apiKey", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          items: [],
          page: 1,
          page_size: 20,
          total_count: 0,
        }),
      ),
    );
    await fetchEvalRuns(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[0]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        run_id: "00000000-0000-0000-0000-000000000099",
        status: "completed",
        metrics_summary: {},
        items: [],
      }),
    );
    await fetchEvalRunDetail(
      JWT_CLIENT,
      "00000000-0000-0000-0000-000000000099",
    );
    expectBearerJwt(vi.mocked(fetch).mock.calls[1]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        run_id: "00000000-0000-0000-0000-000000000099",
        status: "pending",
        created_at: "2026-07-01T12:00:00Z",
      }),
    );
    await triggerEvalRun(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[2]?.[1]);

    vi.mocked(fetch).mockResolvedValue(jsonResponse({ items: [EVAL_PRESET] }));
    await fetchEvalConfigPresets(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[3]?.[1]);

    vi.mocked(fetch).mockResolvedValue(jsonResponse(EVAL_PRESET));
    await createEvalConfigPreset(JWT_CLIENT, {
      name: "baseline",
      config: EVAL_CONFIG,
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[4]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ ...EVAL_PRESET, version: 2 }),
    );
    await updateEvalConfigPreset(JWT_CLIENT, EVAL_PRESET.preset_id, {
      name: "baseline-v2",
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[5]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        ...EVAL_PRESET,
        preset_id: "00000000-0000-0000-0000-0000000000bb",
      }),
    );
    await cloneEvalConfigPreset(JWT_CLIENT, EVAL_PRESET.preset_id);
    expectBearerJwt(vi.mocked(fetch).mock.calls[6]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        run_id: "00000000-0000-0000-0000-000000000099",
        status: "pending",
        created_at: "2026-07-01T12:00:00Z",
      }),
    );
    await triggerPlaygroundEvalRun(JWT_CLIENT, { mode: "golden" });
    expectBearerJwt(vi.mocked(fetch).mock.calls[7]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        items: [{ model_id: "qwen2.5:1.5b-instruct", available: true }],
      }),
    );
    await fetchOllamaModels(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[8]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ points: [], available_metrics: [] }),
    );
    await fetchEvalTimeseries(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[9]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ items: [EVAL_CRITERION] }),
    );
    await fetchEvalCriteria(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[10]?.[1]);

    vi.mocked(fetch).mockResolvedValue(jsonResponse(EVAL_CRITERION));
    await createEvalCriterion(JWT_CLIENT, {
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[11]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ ...EVAL_CRITERION, enabled: false }),
    );
    await updateEvalCriterion(JWT_CLIENT, EVAL_CRITERION.criterion_id, {
      enabled: false,
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[12]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        config_version: 2,
        promoted_at: "2026-07-02T12:00:00Z",
        promoted_by: "44444444-4444-4444-4444-444444444444",
      }),
    );
    await promoteRagConfig(JWT_CLIENT, {
      source: "preset",
      preset_id: EVAL_PRESET.preset_id,
    });
    expectBearerJwt(vi.mocked(fetch).mock.calls[13]?.[1]);

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        config: EVAL_PRESET.config,
        config_version: 1,
      }),
    );
    await fetchActiveRagConfig(JWT_CLIENT);
    expectBearerJwt(vi.mocked(fetch).mock.calls[14]?.[1]);
  });

  it("rag config helpers use apiKey when accessToken is absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          config_version: 1,
          promoted_at: "2026-07-02T12:00:00Z",
          promoted_by: "44444444-4444-4444-4444-444444444444",
        }),
      ),
    );
    await promoteRagConfig(CLIENT, {
      source: "preset",
      preset_id: EVAL_PRESET.preset_id,
    });
    const promoteHeaders = vi.mocked(fetch).mock.calls[0]?.[1]
      ?.headers as Record<string, string>;
    expect(promoteHeaders["Authorization"]).toBe("Bearer test-key");

    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({
        config: EVAL_PRESET.config,
        config_version: 1,
      }),
    );
    await fetchActiveRagConfig(CLIENT);
    const activeHeaders = vi.mocked(fetch).mock.calls[1]?.[1]
      ?.headers as Record<string, string>;
    expect(activeHeaders["Authorization"]).toBe("Bearer test-key");
  });
});
