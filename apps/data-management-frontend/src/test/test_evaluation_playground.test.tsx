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
  if (url.includes("/internal/v1/models/ollama")) {
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });

    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-top-k")).toHaveValue(9);
      expect(screen.getByTestId("eval-playground-system-prompt")).toHaveValue(
        "Preset sandbox prompt.",
      );
      expect(screen.getByTestId("eval-playground-preset-version")).toHaveTextContent(
        "Version 1",
      );
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
          if (url.includes("/internal/v1/eval/config-presets") && method === "POST") {
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
      expect(screen.getByTestId("eval-playground-preset-save")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "my preset" },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-confirm"));

    await waitFor(() => {
      const postCall = vi
        .mocked(globalThis.fetch)
        .mock.calls.find((call) => {
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
      const patchCall = vi
        .mocked(globalThis.fetch)
        .mock.calls.find((call) => {
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
            url.includes(`/internal/v1/eval/config-presets/${PRESET_ID}/clone`) &&
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: PRESET_ID },
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-clone"));

    await waitFor(() => {
      const cloneCall = vi
        .mocked(globalThis.fetch)
        .mock.calls.find((call) => {
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
      expect(screen.getByTestId("eval-playground-preset-save")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    fireEvent.change(screen.getByTestId("eval-playground-preset-name"), {
      target: { value: "broken preset" },
    });
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-preset-confirm")).not.toBeDisabled();
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
      expect(screen.getByTestId("eval-playground-preset-dialog")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-shared"));
    expect(screen.getByTestId("eval-playground-preset-shared")).toBeChecked();
    fireEvent.click(screen.getByTestId("eval-playground-preset-shared"));
    expect(screen.getByTestId("eval-playground-preset-shared")).not.toBeChecked();
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
    await Promise.resolve();
  });

  it("changes the selected Ollama model from the picker", async () => {
    await renderAppRoutesReady("/evaluation?tab=playground");
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-model-id")).toBeInTheDocument();
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
      expect(screen.getByTestId("eval-playground-preset-save")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-save"));
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-preset-dialog")).toBeInTheDocument();
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
      expect(screen.getByTestId("eval-playground-preset-select")).toBeInTheDocument();
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
});
