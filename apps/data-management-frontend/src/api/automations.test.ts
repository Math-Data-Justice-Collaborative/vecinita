/**
 * Automations write-API client (F75 / UJ-080 / TC-252 / TC-255).
 * [Corpus: feature-list.md §F75]
 * [Spec: docs/api-contract.md §EV-027 Automations]
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody, mockFetchUrl } from "@/test/fetch-mock";

import {
  fetchAutomationRuns,
  fetchAutomationsConfig,
  patchAutomationsEnabled,
} from "./automations";

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

describe("automations API client (UJ-080 / TC-252 / TC-255)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchAutomationsConfig GETs /internal/v1/automations/config", async () => {
    const body = {
      enabled: true,
      kill_switch: false,
      max_concurrent: 2,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await fetchAutomationsConfig(CLIENT);

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/automations/config",
    );
    const init = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as
      RequestInit | undefined;
    const headers = init?.headers as Record<string, string> | undefined;
    expect(headers?.["Authorization"]).toBe("Bearer test-key");
  });

  it("fetchAutomationsConfig prefers JWT accessToken (TC-252)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          enabled: false,
          kill_switch: true,
          max_concurrent: 1,
        }),
      ),
    );

    await fetchAutomationsConfig(JWT_CLIENT);
    expectBearerJwt(
      (fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as
        RequestInit | undefined,
    );
  });

  it("fetchAutomationsConfig throws on non-OK", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 503)));
    await expect(fetchAutomationsConfig(CLIENT)).rejects.toThrow(
      /Automations config failed \(503\)/,
    );
  });

  it("patchAutomationsEnabled PATCHes enabled flag (AC-AU1 / TC-252)", async () => {
    const body = {
      enabled: false,
      kill_switch: false,
      max_concurrent: 2,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await patchAutomationsEnabled(JWT_CLIENT, false);

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/automations/config",
    );
    const init = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as
      RequestInit | undefined;
    expect(init?.method).toBe("PATCH");
    expect(mockFetchJsonBody()).toEqual({ enabled: false });
    expectBearerJwt(init);
  });

  it("patchAutomationsEnabled throws on non-OK", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 403)));
    await expect(patchAutomationsEnabled(CLIENT, true)).rejects.toThrow(
      /Automations config update failed \(403\)/,
    );
  });

  it("fetchAutomationRuns GETs paginated history (TC-255)", async () => {
    const body = {
      items: [
        {
          id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          job_type: "automation_catchup",
          status: "completed",
          started_at: "2026-08-07T10:00:00Z",
          finished_at: "2026-08-07T10:01:00Z",
          error: null,
          document_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
          revision: "rev-1",
          created_at: "2026-08-07T10:00:00Z",
          updated_at: "2026-08-07T10:01:00Z",
        },
      ],
      page: 1,
      page_size: 20,
      total_count: 1,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await fetchAutomationRuns(CLIENT, {
      page: 1,
      page_size: 20,
    });

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/automations/runs?page=1&page_size=20",
    );
  });

  it("fetchAutomationRuns throws on non-OK", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 500)));
    await expect(fetchAutomationRuns(CLIENT)).rejects.toThrow(
      /Automation runs failed \(500\)/,
    );
  });

  it("fetchAutomationRuns uses default pagination when params omitted", async () => {
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

    await fetchAutomationRuns(CLIENT);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/automations/runs?page=1&page_size=20",
    );
  });

  it("auth falls back to empty bearer when no token or apiKey", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          enabled: false,
          kill_switch: false,
          max_concurrent: 2,
        }),
      ),
    );

    await fetchAutomationsConfig({ baseUrl: "http://localhost:8002" });
    const init = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as
      RequestInit | undefined;
    const headers = init?.headers as Record<string, string> | undefined;
    expect(headers?.["Authorization"]).toBe("Bearer ");
  });
});
