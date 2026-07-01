import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchEvalRunDetail,
  fetchEvalRuns,
  triggerEvalRun,
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
    await expect(
      fetchEvalRunDetail(OPTIONS, body.run_id),
    ).resolves.toEqual(body);
  });

  it("fetchEvalRunDetail throws when response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    await expect(
      fetchEvalRunDetail(OPTIONS, "missing"),
    ).rejects.toThrow("Eval run detail failed (404)");
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
});
