/**
 * F77 finetune API client (UJ-082 / TC-260–262 / TC-265).
 * [Corpus: feature-list.md §F77]
 * [Spec: docs/api-contract.md §EV-027 Fine-tune]
 * [Corpus: user-journeys.md §UJ-082]
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody, mockFetchUrl } from "@/test/fetch-mock";

import {
  approveFinetuneJob,
  createFinetuneTrainJob,
  fetchFinetuneAdapterPin,
  fetchFinetuneEval,
  listFinetuneJobs,
  promoteFinetuneAdapter,
  rollbackFinetuneAdapter,
} from "./finetune";

const ADMIN = {
  baseUrl: "http://localhost:8001",
  modalKey: "proxy-key",
  accessToken: "jwt-admin",
};

const CORPUS = {
  baseUrl: "http://localhost:8002",
  accessToken: "jwt-admin",
};

const RUN_ID = "11111111-1111-4111-8111-111111111111";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("finetune API client (UJ-082)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("createFinetuneTrainJob POSTs job_type=finetune_train (TC-260)", async () => {
    const body = { job_id: RUN_ID, status: "pending" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body, 202)));

    const result = await createFinetuneTrainJob(ADMIN);

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe("http://localhost:8001/jobs");
    const init = vi.mocked(fetch).mock.calls[0]?.[1] ?? {};
    expect(init.method).toBe("POST");
    expect(typeof init.body).toBe("string");
    expect(JSON.parse(init.body as string)).toEqual({
      urls: [],
      options: { job_type: "finetune_train" },
    });
    const headers = init.headers as Record<string, string>;
    expect(headers["X-Vecinita-Proxy-Key"]).toBe("proxy-key");
    expect(headers["Authorization"]).toBe("Bearer jwt-admin");
  });

  it("approveFinetuneJob POSTs /jobs/{id}/approve (TC-260 / AC-FT2)", async () => {
    const body = {
      job_id: RUN_ID,
      status: "pending",
      job_type: "finetune_train",
      urls: [],
      approved: true,
      created_at: "2026-08-12T00:00:00Z",
      updated_at: "2026-08-12T00:00:00Z",
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await approveFinetuneJob(ADMIN, RUN_ID);

    expect(result.approved).toBe(true);
    expect(result.job_type).toBe("finetune_train");
    expect(mockFetchUrl()).toBe(`http://localhost:8001/jobs/${RUN_ID}/approve`);
    const init = vi.mocked(fetch).mock.calls[0]?.[1] ?? {};
    expect(init.method).toBe("POST");
  });

  it("listFinetuneJobs filters list to finetune_train only", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          jobs: [
            {
              job_id: RUN_ID,
              status: "pending",
              job_type: "finetune_train",
              urls: [],
              approved: false,
              created_at: "2026-08-12T00:00:00Z",
              updated_at: "2026-08-12T00:00:00Z",
            },
            {
              job_id: "22222222-2222-4222-8222-222222222222",
              status: "completed",
              job_type: "ingest",
              urls: ["https://example.com"],
              created_at: "2026-08-12T00:00:00Z",
              updated_at: "2026-08-12T00:00:00Z",
            },
          ],
        }),
      ),
    );

    const jobs = await listFinetuneJobs(ADMIN);

    expect(jobs).toHaveLength(1);
    expect(jobs[0]?.job_type).toBe("finetune_train");
    expect(jobs[0]?.approved).toBe(false);
  });

  it("fetchFinetuneEval GETs base vs adapter report (TC-261)", async () => {
    const body = {
      run_id: RUN_ID,
      adapter_id: "adapter-ui-1",
      base_model_id: "qwen2.5:1.5b-instruct",
      base: {
        faithfulness: 0.7,
        answer_relevancy: 0.6,
        questions_scored: 2,
      },
      adapter: {
        faithfulness: 0.72,
        answer_relevancy: 0.65,
        questions_scored: 2,
      },
      auto_promote: false,
      summary: "Human judgment required",
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await fetchFinetuneEval(CORPUS, RUN_ID);

    expect(result).toEqual(body);
    expect(result.auto_promote).toBe(false);
    expect(mockFetchUrl()).toBe(
      `http://localhost:8002/internal/v1/finetune/runs/${RUN_ID}/eval`,
    );
  });

  it("fetchFinetuneAdapterPin GETs current prod pin (TC-262)", async () => {
    const body = { adapter_id: null, base: true };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await fetchFinetuneAdapterPin(CORPUS);

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/finetune/adapter",
    );
  });

  it("promoteFinetuneAdapter POSTs adapter_id (TC-262 / AC-FT4)", async () => {
    const body = {
      promoted: true,
      adapter_id: "adapter-ui-1",
      base: false,
      auto_promote: false,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await promoteFinetuneAdapter(CORPUS, "adapter-ui-1");

    expect(result).toEqual(body);
    expect(mockFetchUrl()).toBe(
      "http://localhost:8002/internal/v1/finetune/promote",
    );
    expect(mockFetchJsonBody()).toEqual({ adapter_id: "adapter-ui-1" });
  });

  it("rollbackFinetuneAdapter POSTs rollback:true (TC-265 / AC-FT9)", async () => {
    const body = {
      promoted: false,
      adapter_id: null,
      base: true,
      auto_promote: false,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    const result = await rollbackFinetuneAdapter(CORPUS);

    expect(result).toEqual(body);
    expect(mockFetchJsonBody()).toEqual({ rollback: true });
  });

  it("throws on non-OK promote response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 403)));
    await expect(promoteFinetuneAdapter(CORPUS, "adapter-x")).rejects.toThrow(
      /Promote failed/,
    );
  });

  it("throws on non-OK create / approve / list / eval / pin / rollback", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation(() =>
          Promise.resolve(new Response("", { status: 500 })),
        ),
    );
    await expect(createFinetuneTrainJob(ADMIN)).rejects.toThrow(
      /Create finetune job failed/,
    );
    await expect(approveFinetuneJob(ADMIN, RUN_ID)).rejects.toThrow(
      /Approve finetune job failed/,
    );
    await expect(listFinetuneJobs(ADMIN)).rejects.toThrow(
      /List finetune jobs failed/,
    );
    await expect(fetchFinetuneEval(CORPUS, RUN_ID)).rejects.toThrow(
      /Finetune eval failed/,
    );
    await expect(fetchFinetuneAdapterPin(CORPUS)).rejects.toThrow(
      /Finetune adapter pin failed/,
    );
    await expect(rollbackFinetuneAdapter(CORPUS)).rejects.toThrow(
      /Rollback failed/,
    );
  });

  it("uses empty bearer when neither token nor apiKey is set", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ adapter_id: null, base: true })),
    );
    await fetchFinetuneAdapterPin({ baseUrl: "http://localhost:8002" });
    const init = vi.mocked(fetch).mock.calls[0]?.[1];
    expect(init?.headers).toEqual(
      expect.objectContaining({ Authorization: "Bearer " }),
    );
  });
});
