import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

const RUN_ID = "00000000-0000-0000-0000-000000000099";
const NEW_RUN_ID = "00000000-0000-0000-0000-0000000000cc";

const LIST_BODY = {
  items: [
    {
      run_id: RUN_ID,
      status: "completed",
      started_at: "2026-07-01T12:00:00Z",
      completed_at: "2026-07-01T12:01:00Z",
      metrics_summary: {
        retrieval_relevance: 0.91,
        faithfulness: 0.72,
        answer_relevancy: 0.68,
        latency_p95_ms: 4200,
      },
    },
  ],
  page: 1,
  page_size: 20,
  total_count: 1,
};

const CRITERIA_BODY = {
  items: [
    {
      criterion_id: "00000000-0000-0000-0000-000000000077",
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
      scorer_type: "llm_rubric",
      enabled: true,
      created_at: "2026-07-01T10:00:00Z",
      updated_at: "2026-07-01T10:00:00Z",
    },
  ],
};

const OLLAMA_MODELS_BODY = {
  items: [
    {
      model_id: "qwen2.5:1.5b-instruct",
      available: true,
    },
    {
      model_id: "llama3.2:3b",
      available: true,
    },
  ],
};

function defaultPlaygroundFetch(
  url: string,
): Response | { ok: boolean; json: () => Promise<unknown> } {
  if (url.includes("/internal/v1/eval/criteria")) {
    return { ok: true, json: async () => CRITERIA_BODY };
  }
  if (url.includes("/internal/v1/models/ollama")) {
    return { ok: true, json: async () => OLLAMA_MODELS_BODY };
  }
  if (url.includes("/internal/v1/eval/runs/")) {
    return {
      ok: true,
      json: async () => ({
        run_id: RUN_ID,
        status: "completed",
        metrics_summary: LIST_BODY.items[0].metrics_summary,
        items: [],
      }),
    };
  }
  if (url.includes("/internal/v1/eval/runs")) {
    return { ok: true, json: async () => LIST_BODY };
  }
  if (url.includes("/internal/v1/stats")) {
    return {
      ok: true,
      json: async () => ({
        total_documents: 0,
        total_chunks: 0,
        tag_distribution: [],
        language_breakdown: {},
        recent_activity: [],
        top_served: [],
      }),
    };
  }
  if (url.includes("/internal/v1/documents")) {
    return { ok: true, json: async () => [] };
  }
  return { ok: true, json: async () => ({}) };
}

function parsePostBody(init?: RequestInit): Record<string, unknown> | null {
  if (!init?.body || typeof init.body !== "string") return null;
  return JSON.parse(init.body) as Record<string, unknown>;
}

describe("EvaluationPlayground (UJ-045)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders playground tab with two-column layout (UJ-045)", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");

    expect(screen.getByTestId("eval-tab-playground")).toBeInTheDocument();
    expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
    expect(
      screen.getByTestId("eval-playground-config-column"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("eval-playground-run-column"),
    ).toBeInTheDocument();
  });

  it("posts golden batch with config overrides (TC-128)", async () => {
    const overrideTopK = 11;
    const overridePrompt = "Sandbox-only system prompt for golden batch eval.";
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                run_id: NEW_RUN_ID,
                status: "pending",
                created_at: "2026-07-02T12:00:00Z",
              }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-mode-golden"));
    fireEvent.change(screen.getByTestId("eval-playground-top-k"), {
      target: { value: String(overrideTopK) },
    });
    fireEvent.change(screen.getByTestId("eval-playground-system-prompt"), {
      target: { value: overridePrompt },
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));

    await waitFor(() => {
      const postCall = vi
        .mocked(globalThis.fetch)
        .mock.calls.find((call) => {
          const init = call[1];
          const method = (init?.method ?? "GET").toUpperCase();
          return (
            fetchInputUrl(call[0]).includes("/internal/v1/eval/runs") &&
            method === "POST"
          );
        });
      expect(postCall).toBeDefined();
      const body = parsePostBody(postCall?.[1]);
      expect(body?.["mode"]).toBe("golden");
      const config = body?.["config"] as Record<string, unknown> | undefined;
      expect(config?.["top_k"]).toBe(overrideTopK);
      expect(config?.["system_prompt"]).toBe(overridePrompt);
    });
  });

  it("posts ad-hoc single question with mode adhoc (TC-129)", async () => {
    const adhocQuestion = "What are the food pantry hours this week?";
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                run_id: NEW_RUN_ID,
                status: "pending",
                created_at: "2026-07-02T12:00:00Z",
              }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-mode-adhoc"));
    fireEvent.change(screen.getByTestId("eval-playground-adhoc-question"), {
      target: { value: adhocQuestion },
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));

    await waitFor(() => {
      const postCall = vi
        .mocked(globalThis.fetch)
        .mock.calls.find((call) => {
          const init = call[1];
          const method = (init?.method ?? "GET").toUpperCase();
          return (
            fetchInputUrl(call[0]).includes("/internal/v1/eval/runs") &&
            method === "POST"
          );
        });
      expect(postCall).toBeDefined();
      const body = parsePostBody(postCall?.[1]);
      expect(body?.["mode"]).toBe("adhoc");
      expect(body?.["question"]).toBe(adhocQuestion);
    });
  });

  it("loads Ollama models for the model picker (RD-139)", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toBeInTheDocument();
    });
    expect(screen.getByRole("option", { name: /qwen2\.5:1\.5b-instruct/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /llama3\.2:3b/i })).toBeInTheDocument();
  });

  it("disables run button until ad-hoc question is provided (TC-129)", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-mode-adhoc"));
    expect(screen.getByTestId("eval-playground-run-button")).toBeDisabled();

    fireEvent.change(screen.getByTestId("eval-playground-adhoc-question"), {
      target: { value: "Is the community center open on Sundays?" },
    });
    expect(screen.getByTestId("eval-playground-run-button")).not.toBeDisabled();
  });
});
