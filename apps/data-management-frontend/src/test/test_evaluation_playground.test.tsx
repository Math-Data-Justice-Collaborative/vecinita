import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as adminApi from "@/api/admin";
import { fetchInputUrl } from "./fetch-mock";
import {
  renderAppRoutesReady,
  renderSuperAdminAppRoutesReady,
} from "./renderAppHelpers";

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

const ADMIN_USER_ID = "11111111-1111-1111-1111-111111111111";
const OTHER_ADMIN_ID = "33333333-3333-3333-3333-333333333333";
const PRESET_ID = "00000000-0000-0000-0000-0000000000aa";
const CLONED_PRESET_ID = "00000000-0000-0000-0000-0000000000bb";

const SAVED_PRESET_BODY = {
  preset_id: PRESET_ID,
  version: 1,
  name: "baseline",
  config: {
    top_k: 9,
    min_retrieval_score: 0.2,
    system_prompt: "Preset sandbox prompt.",
    max_tokens: 256,
    temperature: 0.2,
    corpus_profile: "fixture",
    criteria_ids: [],
    judge_temperature: 0.2,
    model_id: "qwen2.5:1.5b-instruct",
  },
  shared: true,
  owner_id: OTHER_ADMIN_ID,
  created_at: "2026-07-01T10:00:00Z",
  updated_at: "2026-07-01T10:00:00Z",
};

function defaultPlaygroundFetch(
  url: string,
): Response | { ok: boolean; json: () => Promise<unknown> } {
  if (url.includes("/internal/v1/eval/criteria")) {
    return { ok: true, json: async () => CRITERIA_BODY };
  }
  if (
    url.includes("/internal/v1/models/ollama") &&
    !url.includes("/internal/v1/models/ollama/pull")
  ) {
    return { ok: true, json: async () => OLLAMA_MODELS_BODY };
  }
  if (url.includes("/internal/v1/eval/config-presets")) {
    return { ok: true, json: async () => ({ items: [] }) };
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
      const postCall = vi.mocked(globalThis.fetch).mock.calls.find((call) => {
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
      const postCall = vi.mocked(globalThis.fetch).mock.calls.find((call) => {
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
      expect(
        screen.getByTestId("eval-playground-model-id"),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("option", { name: /qwen2\.5:1\.5b-instruct/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /llama3\.2:3b/i }),
    ).toBeInTheDocument();
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

  it("loads a preset into the config form (TC-127 UI)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [SAVED_PRESET_BODY] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });

    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-top-k")).toHaveValue(9);
      expect(screen.getByTestId("eval-playground-system-prompt")).toHaveValue(
        "Preset sandbox prompt.",
      );
      expect(
        screen.getByTestId("eval-playground-preset-version"),
      ).toHaveTextContent("Version 1");
    });
  });

  it("creates a new preset from current config (TC-127 UI)", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes("/internal/v1/eval/config-presets") &&
            method === "POST"
          ) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                ...SAVED_PRESET_BODY,
                preset_id: CLONED_PRESET_ID,
                name: "my preset",
                owner_id: ADMIN_USER_ID,
                shared: false,
              }),
            });
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({ items: [] }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-save"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "my preset" },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-confirm"));

    await waitFor(() => {
      const postCall = vi.mocked(globalThis.fetch).mock.calls.find((call) => {
        const init = call[1];
        const method = (init?.method ?? "GET").toUpperCase();
        return (
          fetchInputUrl(call[0]).includes("/internal/v1/eval/config-presets") &&
          method === "POST"
        );
      });
      expect(postCall).toBeDefined();
      const body = parsePostBody(postCall?.[1]);
      expect(body?.["name"]).toBe("my preset");
      expect(body?.["shared"]).toBe(false);
    });
  });

  it("updates an owned preset and bumps version (TC-127 UI)", async () => {
    const ownedPreset = {
      ...SAVED_PRESET_BODY,
      owner_id: ADMIN_USER_ID,
      shared: false,
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes(`/internal/v1/eval/config-presets/${PRESET_ID}`) &&
            method === "PATCH"
          ) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                ...ownedPreset,
                version: 2,
                name: "baseline-v2",
              }),
            });
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({ items: [ownedPreset] }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-update"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "baseline-v2" },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-confirm"));

    await waitFor(() => {
      const patchCall = vi.mocked(globalThis.fetch).mock.calls.find((call) => {
        const init = call[1];
        const method = (init?.method ?? "GET").toUpperCase();
        return (
          fetchInputUrl(call[0]).includes(
            `/internal/v1/eval/config-presets/${PRESET_ID}`,
          ) && method === "PATCH"
        );
      });
      expect(patchCall).toBeDefined();
      const body = parsePostBody(patchCall?.[1]);
      expect(body?.["name"]).toBe("baseline-v2");
    });
  });

  it("clones a shared preset from another admin (TC-127 UI)", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes(
              `/internal/v1/eval/config-presets/${PRESET_ID}/clone`,
            ) &&
            method === "POST"
          ) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                ...SAVED_PRESET_BODY,
                preset_id: CLONED_PRESET_ID,
                name: "baseline (copy)",
                owner_id: ADMIN_USER_ID,
                shared: false,
                version: 1,
              }),
            });
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({ items: [SAVED_PRESET_BODY] }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-clone"));

    await waitFor(() => {
      const cloneCall = vi.mocked(globalThis.fetch).mock.calls.find((call) => {
        const init = call[1];
        const method = (init?.method ?? "GET").toUpperCase();
        return (
          fetchInputUrl(call[0]).includes(
            `/internal/v1/eval/config-presets/${PRESET_ID}/clone`,
          ) && method === "POST"
        );
      });
      expect(cloneCall).toBeDefined();
    });
  });

  it("surfaces preset create failure in dialog (TC-127 UI)", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes("/internal/v1/eval/config-presets") &&
            method === "POST"
          ) {
            return Promise.resolve({ ok: false, status: 500 });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-save"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "broken preset" },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-confirm"),
      ).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-confirm"));

    await waitFor(() => {
      expect(screen.getByRole("alert", { hidden: true })).toHaveTextContent(
        /Eval config preset create failed \(500\)/i,
      );
    });
  });

  it("shows shared-by-owner badge for owned shared presets (TC-127 UI)", async () => {
    const ownedSharedPreset = {
      ...SAVED_PRESET_BODY,
      owner_id: ADMIN_USER_ID,
      shared: true,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [ownedSharedPreset] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    await waitFor(() => {
      expect(screen.getByText(/^Shared$/i)).toBeInTheDocument();
    });
  });

  it("updates numeric playground fields and shared checkbox state", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
    });

    fireEvent.change(document.getElementById("eval-playground-min-score")!, {
      target: { value: "0.35" },
    });
    fireEvent.change(document.getElementById("eval-playground-max-tokens")!, {
      target: { value: "512" },
    });
    fireEvent.change(document.getElementById("eval-playground-temperature")!, {
      target: { value: "0.5" },
    });
    fireEvent.change(
      document.getElementById("eval-playground-judge-temperature")!,
      {
        target: { value: "0.4" },
      },
    );

    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-dialog"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-shared"));
    expect(screen.getByTestId("eval-playground-preset-shared")).toBeChecked();
    fireEvent.click(screen.getByTestId("eval-playground-preset-shared"));
    expect(
      screen.getByTestId("eval-playground-preset-shared"),
    ).not.toBeChecked();
  });

  it("surfaces translated preset load failure for non-Error rejections", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
          return Promise.reject("presets offline");
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to load presets/i,
      );
    });
  });

  it("tolerates malformed preset list payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: "not-an-array" }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    expect(screen.getByTestId("eval-playground-preset-select")).toHaveValue("");
  });

  it("surfaces translated model load failure for non-Error rejections", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
          return Promise.reject("models offline");
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to load Ollama models/i,
      );
    });
  });

  it("falls back to vLLM default model when Ollama list returns 503", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return Promise.resolve({ ok: false, status: 503 });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toHaveValue(
        "qwen2.5:1.5b-instruct",
      );
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("falls back to vLLM default model when Ollama list returns 504", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return Promise.resolve({ ok: false, status: 504 });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toHaveValue(
        "qwen2.5:1.5b-instruct",
      );
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("surfaces update preset failure in dialog (TC-127 UI)", async () => {
    const ownedPreset = {
      ...SAVED_PRESET_BODY,
      owner_id: ADMIN_USER_ID,
      shared: false,
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes(`/internal/v1/eval/config-presets/${PRESET_ID}`) &&
            method === "PATCH"
          ) {
            return Promise.resolve({ ok: false, status: 403 });
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({ items: [ownedPreset] }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-update"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "baseline-v2" },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-confirm"));
    await waitFor(() => {
      expect(screen.getByRole("alert", { hidden: true })).toHaveTextContent(
        /Eval config preset update failed \(403\)/i,
      );
    });
  });

  it("ignores preset selection when id is not in the loaded list", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: "00000000-0000-0000-0000-000000000099" },
    });
    expect(screen.getByTestId("eval-playground-top-k")).toHaveValue(5);
  });

  it("ignores stale model load errors after unmount", async () => {
    let rejectModels: ((reason?: unknown) => void) | undefined;
    const modelsGate = new Promise<Response>((_resolve, reject) => {
      rejectModels = reject;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return modelsGate;
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    const view = await renderAppRoutesReady("/evaluation?tab=playground");
    view.unmount();
    rejectModels?.(new Error("models failed after unmount"));
    await modelsGate.catch(() => undefined);
    await Promise.resolve();
  });

  it("changes the selected Ollama model from the picker", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-model-id"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-model-id"), {
      target: { value: "llama3.2:3b" },
    });
    expect(screen.getByTestId("eval-playground-model-id")).toHaveValue(
      "llama3.2:3b",
    );
  });

  it("closes the preset dialog with cancel", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-save"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-dialog"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    await waitFor(() => {
      expect(
        screen.queryByTestId("eval-playground-preset-dialog"),
      ).not.toBeInTheDocument();
    });
  });

  it("persists last preset id when running golden batch with a preset selected (RD-129)", async () => {
    const PLAYGROUND_STORAGE_KEY = "vecinita.eval.playground.v1";
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
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({ items: [SAVED_PRESET_BODY] }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));

    await waitFor(() => {
      const stored = JSON.parse(
        localStorage.getItem(PLAYGROUND_STORAGE_KEY) ?? "{}",
      ) as { lastPresetId?: string };
      expect(stored.lastPresetId).toBe(PRESET_ID);
    });
  });

  it("ignores stale last preset id when preset no longer exists (RD-129)", async () => {
    const PLAYGROUND_STORAGE_KEY = "vecinita.eval.playground.v1";
    localStorage.setItem(
      PLAYGROUND_STORAGE_KEY,
      JSON.stringify({ lastPresetId: PRESET_ID }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-top-k")).toHaveValue(5);
    });
    expect(screen.getByTestId("eval-playground-preset-select")).toHaveValue("");
  });

  it("shows promote button for super-admin and confirms promote (UJ-047)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/rag/config/promote")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              config_version: 3,
              promoted_at: "2026-07-02T12:00:00Z",
              promoted_by: "44444444-4444-4444-4444-444444444444",
            }),
          });
        }
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [SAVED_PRESET_BODY] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-button"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-dialog"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-confirm"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-version"),
      ).toHaveTextContent("3");
    });
  });

  it("closes promote dialog when cancel is clicked", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [SAVED_PRESET_BODY] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-button"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-dialog"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /^Cancel$/i }));
    await waitFor(() => {
      expect(
        screen.queryByTestId("eval-playground-promote-dialog"),
      ).not.toBeInTheDocument();
    });
  });

  it("shows promote failure message when promote API rejects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/rag/config/promote")) {
          return Promise.resolve({
            ok: false,
            status: 403,
            json: async () => ({}),
          });
        }
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [SAVED_PRESET_BODY] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-button"));
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-dialog"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-confirm"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /RAG config promote failed \(403\)/i,
      );
    });
  });

  it("shows generic promote failure when promote throws a non-Error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [SAVED_PRESET_BODY] }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );
    vi.spyOn(adminApi, "promoteRagConfig").mockRejectedValueOnce("offline");

    await renderSuperAdminAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-promote-button"),
      ).not.toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-button"));
    fireEvent.click(screen.getByTestId("eval-playground-promote-confirm"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to promote production config/i,
      );
    });
  });

  it("shows presets load failure when preset fetch rejects", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.reject(new Error("presets offline"));
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/presets offline/i);
    });
  });

  it("shows presets load failure when preset list is invalid", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: "not-an-array" }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-preset-select")).toHaveValue(
        "",
      );
    });
  });

  it("promotes from last run when no preset is selected (super-admin)", async () => {
    let promoteBody: Record<string, unknown> | null = null;
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
          if (
            url.includes("/internal/v1/rag/config/promote") &&
            method === "POST"
          ) {
            promoteBody = parsePostBody(init);
            return Promise.resolve({
              ok: true,
              status: 200,
              json: async () => ({
                config_version: 4,
                promoted_at: "2026-07-02T12:00:00Z",
                promoted_by: "44444444-4444-4444-4444-444444444444",
              }),
            });
          }
          return Promise.resolve(defaultPlaygroundFetch(url));
        }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-run-button")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-last-run")).toHaveTextContent(
        NEW_RUN_ID,
      );
    });
    fireEvent.click(screen.getByTestId("eval-playground-promote-button"));
    fireEvent.click(screen.getByTestId("eval-playground-promote-confirm"));
    await waitFor(() => {
      expect(promoteBody).toEqual({ source: "run", run_id: NEW_RUN_ID });
    });
  });
});

describe("EvaluationPlayground model download (UJ-048)", () => {
  const DOWNLOAD_MODEL_ID = "qwen2.5:3b-instruct";

  const catalogItems = (
    overrides: Partial<Record<string, boolean>> = {},
  ): { model_id: string; available: boolean }[] => [
    { model_id: "qwen2.5:1.5b-instruct", available: overrides["qwen2.5:1.5b-instruct"] ?? true },
    {
      model_id: DOWNLOAD_MODEL_ID,
      available: overrides[DOWNLOAD_MODEL_ID] ?? false,
    },
    { model_id: "qwen2.5:7b-instruct", available: overrides["qwen2.5:7b-instruct"] ?? false },
  ];

  afterEach(() => {
    vi.useRealTimers();
    cleanup();
    vi.restoreAllMocks();
  });

  it("lists undownloaded models as disabled in playground picker", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: catalogItems() }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toBeInTheDocument();
    });
    const option = screen.getByRole("option", {
      name: new RegExp(`${DOWNLOAD_MODEL_ID}.*not downloaded|no descargado`, "i"),
    });
    expect(option).toBeDisabled();
  });

  it("super-admin triggers download and polls until model is available (TC-135)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let listCallCount = 0;
    let pullCalled = false;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        const method = (init?.method ?? "GET").toUpperCase();
        if (url.includes("/internal/v1/models/ollama/pull") && method === "POST") {
          pullCalled = true;
          return Promise.resolve({
            ok: true,
            status: 202,
            json: async () => ({
              job_id: "00000000-0000-0000-0000-0000000000dd",
              model_id: DOWNLOAD_MODEL_ID,
              status: "pulling",
            }),
          });
        }
        if (url.includes("/internal/v1/models/ollama") && method === "GET") {
          listCallCount += 1;
          const available = listCallCount >= 2;
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: catalogItems({ [DOWNLOAD_MODEL_ID]: available }),
            }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );

    await waitFor(() => {
      expect(pullCalled).toBe(true);
    });
    expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
      /checking availability|comprobando/i,
    );

    await vi.advanceTimersByTimeAsync(10_000);
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /available|disponible/i,
      );
    });
  });

  it("hides model download tab for regular admin (TC-136)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("eval-tab-models")).not.toBeInTheDocument();
    expect(screen.queryByTestId("evaluation-models-download")).not.toBeInTheDocument();
  });

  it("surfaces pull failure and poll errors for super-admin", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.spyOn(adminApi, "fetchOllamaModels").mockResolvedValue({
      items: catalogItems(),
    });
    vi.spyOn(adminApi, "pullOllamaModel").mockRejectedValueOnce(
      new Error("Ollama model pull failed (403)"),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(/403/);
    });

    vi.mocked(adminApi.pullOllamaModel).mockResolvedValueOnce({
      job_id: "00000000-0000-0000-0000-0000000000dd",
      model_id: DOWNLOAD_MODEL_ID,
      status: "pulling",
    });
    vi.spyOn(adminApi, "fetchOllamaModels").mockRejectedValueOnce("poll failed");
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await vi.advanceTimersByTimeAsync(10_000);
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /poll failed/i,
      );
    });
  });

  it("shows translated error for non-Error pull rejection", async () => {
    vi.spyOn(adminApi, "fetchOllamaModels").mockResolvedValue({
      items: catalogItems(),
    });
    vi.spyOn(adminApi, "pullOllamaModel").mockRejectedValueOnce("pull failed");
    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /Download failed/i,
      );
    });
  });

  it("shows download timeout after 30 minutes", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const startMs = 1_700_000_000_000;
    vi.setSystemTime(startMs);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        const method = (init?.method ?? "GET").toUpperCase();
        if (url.includes("/internal/v1/models/ollama/pull") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 202,
            json: async () => ({
              job_id: "00000000-0000-0000-0000-0000000000dd",
              model_id: DOWNLOAD_MODEL_ID,
              status: "pulling",
            }),
          });
        }
        if (url.includes("/internal/v1/models/ollama") && method === "GET") {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: catalogItems(),
            }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await vi.advanceTimersByTimeAsync(10_000);
    vi.setSystemTime(startMs + 30 * 60 * 1000 + 1);
    await vi.advanceTimersByTimeAsync(10_000);
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /timed out|superó 30/i,
      );
    });
  });

  it("surfaces poll Error during model download", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.spyOn(adminApi, "pullOllamaModel").mockResolvedValueOnce({
      job_id: "00000000-0000-0000-0000-0000000000dd",
      model_id: DOWNLOAD_MODEL_ID,
      status: "pulling",
    });
    vi.spyOn(adminApi, "fetchOllamaModels")
      .mockResolvedValueOnce({
        items: catalogItems(),
      })
      .mockRejectedValueOnce(new Error("poll list failed"));

    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await vi.advanceTimersByTimeAsync(10_000);
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /poll list failed/i,
      );
    });
  });

  it("clears download poll timer on unmount", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const clearTimeoutSpy = vi.spyOn(globalThis, "clearTimeout");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        const method = (init?.method ?? "GET").toUpperCase();
        if (url.includes("/internal/v1/models/ollama/pull") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 202,
            json: async () => ({
              job_id: "00000000-0000-0000-0000-0000000000dd",
              model_id: DOWNLOAD_MODEL_ID,
              status: "pulling",
            }),
          });
        }
        if (url.includes("/internal/v1/models/ollama") && method === "GET") {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: catalogItems() }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    const view = await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(
        screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
      ).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    );
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /checking availability|comprobando/i,
      );
    });
    view.unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
  });

  it("refreshes catalog and downloads a custom model tag from models tab", async () => {
    let listCallCount = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        const method = (init?.method ?? "GET").toUpperCase();
        if (url.includes("/internal/v1/models/ollama/pull") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 202,
            json: async () => ({
              job_id: "00000000-0000-0000-0000-0000000000dd",
              model_id: "custom:7b-instruct",
              status: "pulling",
            }),
          });
        }
        if (url.includes("/internal/v1/models/ollama") && method === "GET") {
          listCallCount += 1;
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: catalogItems({
                "custom:7b-instruct": listCallCount >= 2,
              }),
            }),
          });
        }
        return Promise.resolve(defaultPlaygroundFetch(url));
      }),
    );

    await renderSuperAdminAppRoutesReady("/evaluation?tab=models");
    await waitFor(() => {
      expect(screen.getByTestId("eval-models-refresh")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-models-refresh"));
    await waitFor(() => {
      expect(listCallCount).toBeGreaterThanOrEqual(2);
    });

    fireEvent.change(screen.getByTestId("eval-models-custom-model-id"), {
      target: { value: "custom:7b-instruct" },
    });
    fireEvent.click(screen.getByTestId("eval-models-custom-download-button"));

    await waitFor(() => {
      expect(screen.getByTestId("eval-models-download-status")).toHaveTextContent(
        /checking availability|comprobando/i,
      );
    });
  });
});
