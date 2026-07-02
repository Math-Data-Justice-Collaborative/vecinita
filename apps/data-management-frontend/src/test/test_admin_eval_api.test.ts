import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createEvalCriterion,
  fetchEvalCriteria,
  fetchEvalRunDetail,
  fetchEvalRuns,
  fetchEvalTimeseries,
  triggerEvalRun,
  updateEvalCriterion,
} from "@/api/admin";

const OPTIONS = {
  baseUrl: "http://localhost:8002",
  apiKey: "test-corpus-key",
};

describe("eval admin API helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("triggerEvalRun accepts staging corpus profile", async () => {
    const created = {
      run_id: "00000000-0000-0000-0000-000000000099",
      status: "pending",
      created_at: "2026-07-01T12:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => created,
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(triggerEvalRun(OPTIONS, "staging")).resolves.toEqual(created);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init?.body).toBe(JSON.stringify({ corpus_profile: "staging" }));
  });

  it("fetchEvalRuns uses accessToken when provided", async () => {
    const body = { items: [], page: 1, page_size: 20, total_count: 0 };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => body,
    });
    vi.stubGlobal("fetch", fetchMock);
    await fetchEvalRuns({
      baseUrl: "http://localhost:8002",
      accessToken: "jwt-token",
    });
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init?.headers).toMatchObject({
      Authorization: "Bearer jwt-token",
    });
  });

  it("fetchEvalRuns returns parsed list on success", async () => {
    const body = { items: [], page: 1, page_size: 20, total_count: 0 };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => body,
      }),
    );
    await expect(fetchEvalRuns(OPTIONS)).resolves.toEqual(body);
  });

  it("fetchEvalRuns throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503 }),
    );
    await expect(fetchEvalRuns(OPTIONS)).rejects.toThrow(
      "Eval runs list failed (503)",
    );
  });

  it("fetchEvalRunDetail returns parsed detail on success", async () => {
    const body = {
      run_id: "00000000-0000-0000-0000-000000000099",
      status: "completed",
      metrics_summary: {},
      items: [],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => body,
      }),
    );
    await expect(fetchEvalRunDetail(OPTIONS, body.run_id)).resolves.toEqual(
      body,
    );
  });

  it("fetchEvalRunDetail throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    await expect(fetchEvalRunDetail(OPTIONS, "missing")).rejects.toThrow(
      "Eval run detail failed (404)",
    );
  });

  it("triggerEvalRun posts fixture profile by default", async () => {
    const created = {
      run_id: "00000000-0000-0000-0000-000000000099",
      status: "pending",
      created_at: "2026-07-01T12:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => created,
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(triggerEvalRun(OPTIONS)).resolves.toEqual(created);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ corpus_profile: "fixture" }));
  });

  it("triggerEvalRun throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500 }),
    );
    await expect(triggerEvalRun(OPTIONS)).rejects.toThrow(
      "Eval run trigger failed (500)",
    );
  });

  it("fetchEvalTimeseries returns parsed series on success", async () => {
    const body = { points: [], available_metrics: ["faithfulness"] };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => body,
      }),
    );
    await expect(fetchEvalTimeseries(OPTIONS, 50)).resolves.toEqual(body);
    expect(vi.mocked(fetch).mock.calls[0]?.[0]).toContain("limit=50");
  });

  it("fetchEvalTimeseries throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 502 }),
    );
    await expect(fetchEvalTimeseries(OPTIONS)).rejects.toThrow(
      "Eval timeseries failed (502)",
    );
  });

  it("fetchEvalCriteria returns parsed list on success", async () => {
    const body = { items: [] };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => body,
      }),
    );
    await expect(fetchEvalCriteria(OPTIONS)).resolves.toEqual(body);
  });

  it("fetchEvalCriteria throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 403 }),
    );
    await expect(fetchEvalCriteria(OPTIONS)).rejects.toThrow(
      "Eval criteria list failed (403)",
    );
  });

  it("createEvalCriterion posts rubric body on success", async () => {
    const created = {
      criterion_id: "00000000-0000-0000-0000-000000000055",
      slug: "tone",
      label: "Tone",
      rubric: "Friendly",
      scorer_type: "llm_rubric" as const,
      enabled: true,
      created_at: "2026-07-01T12:00:00Z",
      updated_at: "2026-07-01T12:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => created,
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      createEvalCriterion(OPTIONS, {
        slug: "tone",
        label: "Tone",
        rubric: "Friendly",
        enabled: false,
      }),
    ).resolves.toEqual(created);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(init?.body).toContain('"enabled":false');
  });

  it("createEvalCriterion throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 400 }),
    );
    await expect(
      createEvalCriterion(OPTIONS, {
        slug: "tone",
        label: "Tone",
        rubric: "Friendly",
      }),
    ).rejects.toThrow("Eval criterion create failed (400)");
  });

  it("updateEvalCriterion patches criterion on success", async () => {
    const updated = {
      criterion_id: "00000000-0000-0000-0000-000000000055",
      slug: "tone",
      label: "Tone",
      rubric: "Friendly",
      scorer_type: "llm_rubric" as const,
      enabled: false,
      created_at: "2026-07-01T12:00:00Z",
      updated_at: "2026-07-01T12:01:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => updated,
      }),
    );
    await expect(
      updateEvalCriterion(OPTIONS, updated.criterion_id, { enabled: false }),
    ).resolves.toEqual(updated);
  });

  it("updateEvalCriterion throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 409 }),
    );
    await expect(
      updateEvalCriterion(OPTIONS, "missing", { enabled: true }),
    ).rejects.toThrow("Eval criterion update failed (409)");
  });

  it("eval API helpers send an empty bearer when no token or apiKey is set", async () => {
    const noAuth = { baseUrl: "http://localhost:8002" };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchEvalRuns(noAuth);
    await fetchEvalRunDetail(noAuth, "run-1");
    await triggerEvalRun(noAuth);
    await fetchEvalTimeseries(noAuth);
    await fetchEvalCriteria(noAuth);
    await createEvalCriterion(noAuth, {
      slug: "tone",
      label: "Tone",
      rubric: "Friendly",
    });
    await updateEvalCriterion(noAuth, "crit-1", { enabled: true });

    for (const call of fetchMock.mock.calls) {
      const init = call[1] as RequestInit | undefined;
      const headers = init?.headers as Record<string, string> | undefined;
      expect(headers?.Authorization).toBe("Bearer ");
    }
    expect(String(fetchMock.mock.calls[3]?.[0])).toContain("limit=100");
  });
});
