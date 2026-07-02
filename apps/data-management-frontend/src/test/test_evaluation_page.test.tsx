import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

const RUN_ID = "00000000-0000-0000-0000-000000000099";
const RUN_ID_B = "00000000-0000-0000-0000-000000000088";

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

const DETAIL_BODY = {
  run_id: RUN_ID,
  status: "completed",
  metrics_summary: LIST_BODY.items[0].metrics_summary,
  items: [
    {
      case_id: "community-food-pantry",
      locale: "en",
      question: "When are food pantry hours updated?",
      expected_doc_url: "fixture://corpus/en/community-resources.md",
      retrieved_urls: ["fixture://corpus/en/community-resources.md"],
      answer: "Food pantry hours are posted weekly.",
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.85,
        answer_relevancy: 0.8,
        latency_ms: 3100,
      },
    },
    {
      case_id: "edge-abstain-mayor-phone",
      locale: "en",
      question: "What is the mayor's personal phone number?",
      retrieved_urls: [],
      answer:
        "I don't have enough community corpus context to answer that question.",
      metrics: {
        retrieval_pass: true,
        faithfulness: null,
        answer_relevancy: null,
        latency_ms: 1200,
      },
    },
    {
      case_id: "retrieval-miss",
      locale: "en",
      question: "Where is the wrong document?",
      retrieved_urls: [],
      answer: null,
      metrics: {
        retrieval_pass: false,
        faithfulness: 0.4,
        answer_relevancy: 0.3,
        latency_ms: 900,
      },
    },
  ],
};

function defaultEvalFetch(
  url: string,
): Response | { ok: boolean; json: () => Promise<unknown> } {
  if (url.includes("/internal/v1/eval/criteria")) {
    return { ok: true, json: async () => ({ items: [] }) };
  }
  if (url.includes("/internal/v1/eval/config-presets")) {
    return { ok: true, json: async () => ({ items: [] }) };
  }
  if (url.includes("/internal/v1/models/ollama")) {
    return {
      ok: true,
      json: async () => ({
        items: [{ model_id: "qwen2.5:1.5b-instruct", available: true }],
      }),
    };
  }
  if (url.includes("/internal/v1/eval/runs/")) {
    return {
      ok: true,
      json: async () => DETAIL_BODY,
    };
  }
  if (url.includes("/internal/v1/eval/runs")) {
    return {
      ok: true,
      json: async () => LIST_BODY,
    };
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

const PLAYGROUND_STORAGE_KEY = "vecinita.eval.playground.v1";
const LAST_PRESET_ID = "00000000-0000-0000-0000-0000000000aa";

async function openPlaygroundFromRunButton(): Promise<void> {
  fireEvent.click(screen.getByTestId("evaluation-run-button"));
  await waitFor(() => {
    expect(screen.getByTestId("evaluation-playground")).toBeInTheDocument();
  });
}

async function triggerPlaygroundGoldenRun(): Promise<void> {
  await openPlaygroundFromRunButton();
  fireEvent.click(screen.getByTestId("eval-playground-run-button"));
}

describe("EvaluationPage", () => {
  beforeEach(() => {
    localStorage.removeItem(PLAYGROUND_STORAGE_KEY);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    localStorage.removeItem(PLAYGROUND_STORAGE_KEY);
    vi.restoreAllMocks();
  });

  it("navigates to playground when Run evaluation is clicked (RD-129)", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-run-button")).toBeInTheDocument();
    });
    await openPlaygroundFromRunButton();
    expect(screen.getByTestId("eval-tab-playground")).toHaveAttribute(
      "data-state",
      "active",
    );
  });

  it("loads last-used preset when opening playground from Run evaluation (RD-129)", async () => {
    localStorage.setItem(
      PLAYGROUND_STORAGE_KEY,
      JSON.stringify({ lastPresetId: LAST_PRESET_ID }),
    );
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  preset_id: LAST_PRESET_ID,
                  version: 1,
                  name: "saved baseline",
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
                  shared: false,
                  owner_id: "11111111-1111-1111-1111-111111111111",
                  created_at: "2026-07-01T10:00:00Z",
                  updated_at: "2026-07-01T10:00:00Z",
                },
              ],
            }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await openPlaygroundFromRunButton();
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-top-k")).toHaveValue(9);
      expect(screen.getByTestId("eval-playground-system-prompt")).toHaveValue(
        "Preset sandbox prompt.",
      );
    });
  });

  it("loads history and per-question drill-down (TC-116)", async () => {
    await renderAppRoutesReady("/evaluation");

    expect(screen.getByTestId("evaluation-page")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-drilldown")).toBeInTheDocument();
    });
    expect(screen.getByText(/91%/)).toBeInTheDocument();
    expect(
      screen.getByText(/When are food pantry hours updated\?/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Food pantry hours are posted weekly\./),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Pass/i).length).toBeGreaterThan(0);
  });

  it("renders faithfulness and answer relevancy scores from API (TC-116)", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-drilldown")).toBeInTheDocument();
    });
    expect(screen.getByText("0.85")).toBeInTheDocument();
    expect(screen.getByText("0.80")).toBeInTheDocument();
    expect(screen.getByText("0.72")).toBeInTheDocument();
    expect(screen.getByText("0.68")).toBeInTheDocument();
  });

  it("shows model answers and column controls in drill-down", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-drilldown")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId("eval-drilldown-columns-toggle"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("eval-drilldown-wrap-toggle"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("eval-answer-community-food-pantry-en"),
    ).toHaveTextContent(/Food pantry hours are posted weekly\./);
  });

  it("shows hint when judge metrics are null with zero retrieval", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs/")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...DETAIL_BODY,
              metrics_summary: {
                retrieval_relevance: 0,
                faithfulness: null,
                answer_relevancy: null,
                latency_p95_ms: 1599,
              },
              items: DETAIL_BODY.items.map((item) => ({
                ...item,
                retrieved_urls: [],
                answer:
                  "I don't have enough community corpus context to answer that question.",
                metrics: {
                  ...item.metrics,
                  retrieval_pass: false,
                  faithfulness: null,
                  answer_relevancy: null,
                },
              })),
            }),
          });
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...LIST_BODY,
              items: [
                {
                  ...LIST_BODY.items[0],
                  metrics_summary: {
                    retrieval_relevance: 0,
                    faithfulness: null,
                    answer_relevancy: null,
                    latency_p95_ms: 1599,
                  },
                },
              ],
            }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(
        screen.getByTestId("evaluation-judges-skipped-hint"),
      ).toBeInTheDocument();
    });
  });

  it("prepends a new run to history immediately after create (TC-123)", async () => {
    const NEW_RUN_ID = "00000000-0000-0000-0000-0000000000bb";
    let releasePoll: (() => void) | undefined;
    const pollGate = new Promise<void>((resolve) => {
      releasePoll = resolve;
    });
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
          if (url.includes(`/internal/v1/eval/runs/${NEW_RUN_ID}`)) {
            return pollGate.then(() => ({
              ok: true,
              json: async () => ({
                ...DETAIL_BODY,
                run_id: NEW_RUN_ID,
                status: "completed",
              }),
            }));
          }
          if (url.includes("/internal/v1/eval/runs/")) {
            return Promise.resolve({
              ok: true,
              json: async () => DETAIL_BODY,
            });
          }
          if (url.includes("/internal/v1/eval/runs")) {
            return Promise.resolve({
              ok: true,
              json: async () => LIST_BODY,
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-run-button")).toBeInTheDocument();
    });
    await openPlaygroundFromRunButton();
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-last-run")).toHaveTextContent(
        NEW_RUN_ID,
      );
    });
    await waitFor(() => {
      const history = screen.getByTestId("evaluation-history");
      expect(within(history).getByText(NEW_RUN_ID)).toBeInTheDocument();
      expect(within(history).getByText(/Pending/i)).toBeInTheDocument();
    });
    releasePoll?.();
    fireEvent.click(screen.getByTestId("eval-tab-runs"));
    await waitFor(() => {
      expect(screen.getByText(/Completed/i)).toBeInTheDocument();
    });
  });

  it("triggers a new eval run from playground and posts to the API", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-run-button")).toBeInTheDocument();
    });

    await triggerPlaygroundGoldenRun();

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
    const calls = vi.mocked(globalThis.fetch).mock.calls;
    const postCall = calls.find((call) => {
      const init = call[1];
      const method = (init?.method ?? "GET").toUpperCase();
      return (
        fetchInputUrl(call[0]).includes("/internal/v1/eval/runs") &&
        method === "POST"
      );
    });
    expect(postCall).toBeDefined();
  });

  it("shows empty history when no eval runs exist", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByText(/no evaluation runs yet/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("evaluation-drilldown"),
    ).not.toBeInTheDocument();
  });

  it("surfaces load errors from the eval API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({ ok: false, status: 503 });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Eval runs list failed/i,
      );
    });
  });

  it("renders pending, running, and failed status badges", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs/")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...DETAIL_BODY,
              status: "failed",
              metrics_summary: {},
              items: [],
            }),
          });
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                { run_id: RUN_ID, status: "pending", metrics_summary: {} },
                { run_id: RUN_ID_B, status: "running", metrics_summary: {} },
                {
                  run_id: "00000000-0000-0000-0000-000000000077",
                  status: "failed",
                  metrics_summary: {},
                },
              ],
              page: 1,
              page_size: 20,
              total_count: 3,
            }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByText(/Pending/i)).toBeInTheDocument();
      expect(screen.getByText(/Running/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Failed/i).length).toBeGreaterThan(0);
    });
  });

  it("highlights low metrics and retrieval failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs/")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              ...DETAIL_BODY,
              metrics_summary: {
                retrieval_relevance: 0.5,
                faithfulness: 0.55,
                answer_relevancy: null,
                latency_p95_ms: null,
              },
            }),
          });
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => LIST_BODY,
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByText(/50%/)).toBeInTheDocument();
      expect(screen.getByText(/0\.55/)).toBeInTheDocument();
      expect(screen.getAllByText(/Fail/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/—/).length).toBeGreaterThan(0);
    });
  });

  it("loads a different run when a history row is selected", async () => {
    const detailForB = {
      ...DETAIL_BODY,
      run_id: RUN_ID_B,
      items: [
        {
          case_id: "other-case",
          locale: "en",
          question: "Second run question?",
          retrieved_urls: [],
          metrics: {
            retrieval_pass: true,
            faithfulness: 0.9,
            answer_relevancy: 0.9,
            latency_ms: 100,
          },
        },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          if (url.includes(`/internal/v1/eval/runs/${RUN_ID_B}`)) {
            return Promise.resolve({
              ok: true,
              json: async () => detailForB,
            });
          }
          if (url.includes("/internal/v1/eval/runs/")) {
            return Promise.resolve({
              ok: true,
              json: async () => DETAIL_BODY,
            });
          }
          if (url.includes("/internal/v1/eval/runs")) {
            const method = (init?.method ?? "GET").toUpperCase();
            if (method === "POST") {
              return Promise.resolve({
                ok: true,
                json: async () => ({
                  run_id: RUN_ID,
                  status: "pending",
                  created_at: "2026-07-01T12:00:00Z",
                }),
              });
            }
            return Promise.resolve({
              ok: true,
              json: async () => ({
                items: [
                  LIST_BODY.items[0],
                  {
                    run_id: RUN_ID_B,
                    status: "completed",
                    metrics_summary: {},
                  },
                ],
                page: 1,
                page_size: 20,
                total_count: 2,
              }),
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByText(RUN_ID_B)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText(RUN_ID_B));
    await waitFor(() => {
      expect(screen.getByText(/Second run question\?/)).toBeInTheDocument();
    });
  });

  it("refreshes history when the refresh button is clicked", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });
    const callsBefore = vi.mocked(globalThis.fetch).mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    await waitFor(() => {
      expect(vi.mocked(globalThis.fetch).mock.calls.length).toBeGreaterThan(
        callsBefore,
      );
    });
  });

  it("shows an error when triggering a playground eval run fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            return Promise.resolve({ ok: false, status: 500 });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await triggerPlaygroundGoldenRun();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Eval run trigger failed \(500\)/i,
      );
    });
  });

  it("polls a pending run until it completes", async () => {
    const POLL_RUN_ID = "00000000-0000-0000-0000-0000000000aa";
    let pollDetailCalls = 0;
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
                run_id: POLL_RUN_ID,
                status: "pending",
                created_at: "2026-07-01T12:00:00Z",
              }),
            });
          }
          if (url.includes(`/internal/v1/eval/runs/${POLL_RUN_ID}`)) {
            pollDetailCalls += 1;
            const status = pollDetailCalls < 2 ? "running" : "completed";
            return Promise.resolve({
              ok: true,
              json: async () => ({
                ...DETAIL_BODY,
                run_id: POLL_RUN_ID,
                status,
              }),
            });
          }
          if (url.includes("/internal/v1/eval/runs/")) {
            return Promise.resolve({
              ok: true,
              json: async () => DETAIL_BODY,
            });
          }
          if (url.includes("/internal/v1/eval/runs")) {
            return Promise.resolve({
              ok: true,
              json: async () => LIST_BODY,
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await triggerPlaygroundGoldenRun();
    await waitFor(
      () => {
        expect(pollDetailCalls).toBeGreaterThanOrEqual(2);
      },
      { timeout: 3000 },
    );
  });

  it("falls back to translated load error for non-Error rejections", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs")) {
          // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
          return Promise.reject("offline");
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to load evaluation runs/i,
      );
    });
  });

  it("stops polling when a playground-triggered run fails", async () => {
    let detailCalls = 0;
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
                run_id: RUN_ID,
                status: "pending",
                created_at: "2026-07-01T12:00:00Z",
              }),
            });
          }
          if (url.includes("/internal/v1/eval/runs/")) {
            detailCalls += 1;
            return Promise.resolve({
              ok: true,
              json: async () => ({
                ...DETAIL_BODY,
                status: "failed",
                items: [],
                error_message:
                  "embed failed with status 404: modal-http: invalid function call",
              }),
            });
          }
          if (url.includes("/internal/v1/eval/runs")) {
            return Promise.resolve({
              ok: true,
              json: async () => LIST_BODY,
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await triggerPlaygroundGoldenRun();
    await waitFor(() => {
      expect(detailCalls).toBeGreaterThanOrEqual(1);
      expect(screen.getByTestId("evaluation-run-error")).toHaveTextContent(
        "modal-http: invalid function call",
      );
    });
  });

  it("shows running label while a playground eval run is in flight", async () => {
    let resolvePost: (() => void) | undefined;
    const postGate = new Promise<void>((resolve) => {
      resolvePost = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            return postGate.then(() => ({
              ok: true,
              json: async () => ({
                run_id: RUN_ID,
                status: "pending",
                created_at: "2026-07-01T12:00:00Z",
              }),
            }));
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await openPlaygroundFromRunButton();
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByText(/Starting run…/)).toBeInTheDocument();
    });
    resolvePost?.();
    await waitFor(() => {
      expect(screen.queryByText(/Starting run…/)).not.toBeInTheDocument();
    });
  });

  it("shows loading text before the first history response", async () => {
    let releaseList: (() => void) | undefined;
    const listGate = new Promise<void>((resolve) => {
      releaseList = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (
          url.includes("/internal/v1/eval/runs") &&
          !url.includes("/internal/v1/eval/runs/")
        ) {
          return listGate.then(() => ({
            ok: true,
            json: async () => LIST_BODY,
          }));
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    await renderAppRoutesReady("/evaluation");
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
    releaseList?.();
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });
  });

  it("uses translated playground trigger error for non-Error rejections", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("offline");
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );
    await renderAppRoutesReady("/evaluation");
    await triggerPlaygroundGoldenRun();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to start playground run/i,
      );
    });
  });

  it("ignores in-flight history updates after unmount", async () => {
    let releaseList: (() => void) | undefined;
    const listGate = new Promise<void>((resolve) => {
      releaseList = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (
          url.includes("/internal/v1/eval/runs") &&
          !url.includes("/internal/v1/eval/runs/")
        ) {
          return listGate.then(() => ({
            ok: true,
            json: async () => LIST_BODY,
          }));
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    const view = await renderAppRoutesReady("/evaluation");
    view.unmount();
    releaseList?.();
    await Promise.resolve();
  });

  it("ignores in-flight history updates after unmount", async () => {
    let releaseDetail: (() => void) | undefined;
    const detailGate = new Promise<void>((resolve) => {
      releaseDetail = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes(`/internal/v1/eval/runs/${RUN_ID}`)) {
          return detailGate.then(() => ({
            ok: true,
            json: async () => DETAIL_BODY,
          }));
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => LIST_BODY,
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    const view = await renderAppRoutesReady("/evaluation");
    view.unmount();
    releaseDetail?.();
    await Promise.resolve();
  });

  it("ignores load errors after unmount", async () => {
    let rejectList: ((reason?: unknown) => void) | undefined;
    const listGate = new Promise<Response>((_resolve, reject) => {
      rejectList = reject;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (
          url.includes("/internal/v1/eval/runs") &&
          !url.includes("/internal/v1/eval/runs/")
        ) {
          return listGate;
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
    const view = await renderAppRoutesReady("/evaluation");
    view.unmount();
    rejectList?.(new Error("load failed after unmount"));
    await Promise.resolve();
  });
});
