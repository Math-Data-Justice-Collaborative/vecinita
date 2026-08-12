/**
 * UJ-082 / T129.9 — DM FT UI: approve train, eval evidence, human promote.
 *
 * [Corpus: feature-list.md §F77]
 * [Corpus: user-journeys.md §UJ-082]
 * [Spec: docs/test-plan.md §TC-260 §TC-261 §TC-262 §TC-265]
 * [Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT3 §AC-FT4 §AC-FT9]
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { FinetunePage } from "@/pages/FinetunePage";

import { fetchInputUrl } from "./fetch-mock";
import { renderWithProviders } from "./renderWithProviders";

const RUN_ID = "11111111-1111-4111-8111-111111111111";

const PENDING_JOB = {
  job_id: RUN_ID,
  status: "pending",
  job_type: "finetune_train",
  urls: [] as string[],
  approved: false,
  created_at: "2026-08-12T10:00:00.000Z",
  updated_at: "2026-08-12T10:00:00.000Z",
};

const COMPLETED_JOB = {
  ...PENDING_JOB,
  status: "completed",
  approved: true,
  metrics: {
    finetune_outcome: "trained",
    adapter_id: "adapter-ui-1",
    adapter_path: "/adapters/adapter-ui-1",
    pair_count: 8,
    base_model_id: "qwen2.5:1.5b-instruct",
  },
};

const EVAL_REPORT = {
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
  summary:
    "Human judgment required — no automated promote (RD-338 / AC-FT4). Promote only when the operator judges the adapter better than base.",
};

const PIN_BASE = { adapter_id: null, base: true };

function jsonOk(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

function renderFinetune() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/finetune"]}>
        <Routes>
          <Route path="/finetune" element={<FinetunePage />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

function stubFinetuneApis(opts?: {
  jobs?: unknown[];
  pin?: { adapter_id: string | null; base: boolean };
  onApprove?: () => void;
  onPromote?: (body: unknown) => void;
  onCreate?: () => void;
}) {
  let jobs = [...(opts?.jobs ?? [PENDING_JOB])];
  let pin = opts?.pin ?? PIN_BASE;

  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        const method = init?.method ?? "GET";

        if (url.endsWith("/jobs") && method === "GET") {
          return Promise.resolve(jsonOk({ jobs }));
        }
        if (url.endsWith("/jobs") && method === "POST") {
          opts?.onCreate?.();
          const created = {
            job_id: "33333333-3333-4333-8333-333333333333",
            status: "pending",
          };
          jobs = [
            {
              ...PENDING_JOB,
              job_id: created.job_id,
              approved: false,
            },
            ...jobs,
          ];
          return Promise.resolve(jsonOk(created, 202));
        }
        if (url.includes("/approve") && method === "POST") {
          opts?.onApprove?.();
          jobs = jobs.map((j) => {
            const job = j as typeof PENDING_JOB;
            if (job.job_id === RUN_ID) {
              return { ...job, approved: true };
            }
            return job;
          });
          return Promise.resolve(jsonOk({ ...PENDING_JOB, approved: true }));
        }
        if (url.includes("/finetune/adapter") && method === "GET") {
          return Promise.resolve(jsonOk(pin));
        }
        if (url.includes("/finetune/runs/") && url.includes("/eval")) {
          return Promise.resolve(jsonOk(EVAL_REPORT));
        }
        if (url.includes("/finetune/promote") && method === "POST") {
          const rawBody = init?.body;
          if (typeof rawBody !== "string") {
            return Promise.resolve(jsonOk({ detail: "bad body" }, 400));
          }
          const body = JSON.parse(rawBody) as {
            adapter_id?: string;
            rollback?: boolean;
          };
          opts?.onPromote?.(body);
          if (body.rollback) {
            pin = { adapter_id: null, base: true };
            return Promise.resolve(
              jsonOk({
                promoted: false,
                adapter_id: null,
                base: true,
                auto_promote: false,
              }),
            );
          }
          pin = { adapter_id: body.adapter_id ?? null, base: false };
          return Promise.resolve(
            jsonOk({
              promoted: true,
              adapter_id: body.adapter_id,
              base: false,
              auto_promote: false,
            }),
          );
        }
        return Promise.resolve(jsonOk({}));
      }),
  );
}

describe("UJ-082 Fine-tune UI (T129.9)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy-key");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("shows prod pin as base and lists pending train jobs (TC-262)", async () => {
    stubFinetuneApis();
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-admin-page")).toBeInTheDocument();
    });
    expect(screen.getByTestId("finetune-prod-pin")).toHaveTextContent(/base/i);
    expect(screen.getByTestId("finetune-job-row")).toBeInTheDocument();
    expect(screen.getByTestId("finetune-approve-btn")).toBeEnabled();
  });

  it("TC-260: Approve train POSTs /jobs/{id}/approve", async () => {
    const onApprove = vi.fn();
    stubFinetuneApis({ onApprove });
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-approve-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-approve-btn"));

    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(
        screen.queryByTestId("finetune-approve-btn"),
      ).not.toBeInTheDocument();
    });
  });

  it("Request train POSTs finetune_train job", async () => {
    const onCreate = vi.fn();
    stubFinetuneApis({ jobs: [], onCreate });
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-request-train-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-request-train-btn"));

    await waitFor(() => {
      expect(onCreate).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByTestId("finetune-job-row")).toBeInTheDocument();
    });
  });

  it("TC-261: View eval shows base vs adapter and human-judgment summary", async () => {
    stubFinetuneApis({ jobs: [COMPLETED_JOB] });
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("finetune-eval-report")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId("finetune-eval-base-faithfulness"),
    ).toHaveTextContent("0.7");
    expect(
      screen.getByTestId("finetune-eval-adapter-faithfulness"),
    ).toHaveTextContent("0.72");
    expect(screen.getByTestId("finetune-auto-promote")).toHaveTextContent(
      /false|off|no/i,
    );
    expect(screen.getByTestId("finetune-eval-summary")).toHaveTextContent(
      /human judgment/i,
    );
  });

  it("TC-262 / AC-FT4: Promote stays disabled until operator confirms judgment", async () => {
    const onPromote = vi.fn();
    stubFinetuneApis({ jobs: [COMPLETED_JOB], onPromote });
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("finetune-promote-btn")).toBeDisabled();
    });

    fireEvent.click(screen.getByTestId("finetune-promote-confirm"));
    expect(screen.getByTestId("finetune-promote-btn")).toBeEnabled();

    fireEvent.click(screen.getByTestId("finetune-promote-btn"));

    await waitFor(() => {
      expect(onPromote).toHaveBeenCalledWith({ adapter_id: "adapter-ui-1" });
    });
    await waitFor(() => {
      expect(screen.getByTestId("finetune-prod-pin")).toHaveTextContent(
        /adapter-ui-1/,
      );
    });
  });

  it("TC-265 / AC-FT9: Rollback clears prod pin to base", async () => {
    const onPromote = vi.fn();
    stubFinetuneApis({
      jobs: [COMPLETED_JOB],
      pin: { adapter_id: "adapter-ui-1", base: false },
      onPromote,
    });
    renderFinetune();

    await waitFor(() => {
      expect(screen.getByTestId("finetune-prod-pin")).toHaveTextContent(
        /adapter-ui-1/,
      );
    });
    fireEvent.click(screen.getByTestId("finetune-rollback-btn"));

    await waitFor(() => {
      expect(onPromote).toHaveBeenCalledWith({ rollback: true });
    });
    await waitFor(() => {
      expect(screen.getByTestId("finetune-prod-pin")).toHaveTextContent(
        /base/i,
      );
    });
  });

  it("shows empty jobs and load error states", async () => {
    stubFinetuneApis({ jobs: [] });
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-jobs-empty")).toBeInTheDocument();
    });
    cleanup();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({}),
        text: async () => "down",
      }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("surfaces approve failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(jsonOk({ jobs: [PENDING_JOB] }));
          }
          if (url.includes("/finetune/adapter")) {
            return Promise.resolve(jsonOk(PIN_BASE));
          }
          if (url.includes("/approve")) {
            return Promise.resolve({
              ok: false,
              status: 403,
              text: async () => "forbidden",
              json: async () => ({}),
            });
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-approve-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-approve-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/forbidden/i);
    });
  });

  it("surfaces eval failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(jsonOk({ jobs: [COMPLETED_JOB] }));
          }
          if (url.includes("/finetune/adapter")) {
            return Promise.resolve(jsonOk(PIN_BASE));
          }
          if (url.includes("/eval")) {
            return Promise.resolve({
              ok: false,
              status: 404,
              json: async () => ({}),
            });
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/eval failed/i);
    });
  });

  it("surfaces promote and rollback failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(jsonOk({ jobs: [COMPLETED_JOB] }));
          }
          if (url.includes("/finetune/adapter") && method === "GET") {
            return Promise.resolve(
              jsonOk({ adapter_id: "adapter-ui-1", base: false }),
            );
          }
          if (url.includes("/eval")) {
            return Promise.resolve(jsonOk(EVAL_REPORT));
          }
          if (url.includes("/finetune/promote")) {
            return Promise.resolve({
              ok: false,
              status: 500,
              json: async () => ({}),
            });
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));
    await waitFor(() => {
      expect(
        screen.getByTestId("finetune-promote-confirm"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("finetune-promote-confirm"));
    fireEvent.click(screen.getByTestId("finetune-promote-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/Promote failed/i);
    });

    fireEvent.click(screen.getByTestId("finetune-rollback-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/Rollback failed/i);
    });
  });

  it("refresh reloads pin and jobs", async () => {
    stubFinetuneApis();
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-job-row")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /refresh fine-tune/i }));
    await waitFor(() => {
      expect(screen.getByTestId("finetune-prod-pin")).toBeInTheDocument();
    });
  });

  it("covers error fallbacks, failed badge, null metrics, auto-promote on", async () => {
    const failedJob = {
      ...PENDING_JOB,
      job_id: "44444444-4444-4444-8444-444444444444",
      status: "failed",
      approved: true,
      metrics: null,
    };
    const reportNullMetrics = {
      ...EVAL_REPORT,
      auto_promote: true,
      base: {
        faithfulness: null,
        answer_relevancy: null,
        questions_scored: 0,
      },
      adapter: {
        faithfulness: null,
        answer_relevancy: null,
        questions_scored: 0,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(
              jsonOk({
                jobs: [
                  failedJob,
                  COMPLETED_JOB,
                  {
                    ...PENDING_JOB,
                    job_id: "55555555-5555-4555-8555-555555555555",
                    approved: null,
                    status: "running",
                  },
                ],
              }),
            );
          }
          if (url.endsWith("/jobs") && method === "POST") {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("enqueue refused");
          }
          if (url.includes("/finetune/adapter")) {
            return Promise.resolve(jsonOk(PIN_BASE));
          }
          if (url.includes("/eval")) {
            return Promise.resolve(jsonOk(reportNullMetrics));
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByText("failed")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("finetune-request-train-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/request/i);
    });
    const viewEval = screen.getAllByTestId("finetune-view-eval-btn")[0];
    expect(viewEval).toBeDefined();
    fireEvent.click(viewEval!);
    await waitFor(() => {
      expect(screen.getByTestId("finetune-eval-report")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId("finetune-eval-base-faithfulness"),
    ).toHaveTextContent("—");
    expect(screen.getByTestId("finetune-auto-promote")).toHaveTextContent(
      /on/i,
    );
  });

  it("shows i18n fallbacks for non-Error action failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(
              jsonOk({ jobs: [PENDING_JOB, COMPLETED_JOB] }),
            );
          }
          if (url.includes("/finetune/adapter") && method === "GET") {
            return Promise.resolve(
              jsonOk({ adapter_id: "adapter-ui-1", base: false }),
            );
          }
          if (url.includes("/approve")) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("approve refused");
          }
          if (url.includes("/eval")) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("eval refused");
          }
          if (url.includes("/finetune/promote")) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("promote refused");
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-approve-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-approve-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/approve/i);
    });

    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/eval/i);
    });

    // Successful eval then non-Error promote/rollback
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(jsonOk({ jobs: [COMPLETED_JOB] }));
          }
          if (url.includes("/finetune/adapter") && method === "GET") {
            return Promise.resolve(
              jsonOk({ adapter_id: "adapter-ui-1", base: false }),
            );
          }
          if (url.includes("/eval")) {
            return Promise.resolve(jsonOk(EVAL_REPORT));
          }
          if (url.includes("/finetune/promote")) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("promote refused");
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    cleanup();
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));
    await waitFor(() => {
      expect(
        screen.getByTestId("finetune-promote-confirm"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("finetune-promote-confirm"));
    fireEvent.click(screen.getByTestId("finetune-promote-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/promote/i);
    });
    fireEvent.click(screen.getByTestId("finetune-rollback-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /roll back|rollback/i,
      );
    });
  });

  it("ignores late load results after unmount", async () => {
    let resolveJobs: ((value: unknown) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/finetune/adapter")) {
          return Promise.resolve(jsonOk(PIN_BASE));
        }
        if (url.endsWith("/jobs")) {
          return new Promise((resolve) => {
            resolveJobs = resolve;
          });
        }
        return Promise.resolve(jsonOk({}));
      }),
    );
    const { unmount } = renderFinetune();
    await waitFor(() => {
      expect(resolveJobs).toBeDefined();
    });
    unmount();
    resolveJobs?.(jsonOk({ jobs: [PENDING_JOB] }));
  });

  it("shows loadFailed when load rejects a non-Error value", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue("backend down"));
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load/i);
    });
  });

  it("shows Error message when request train rejects an Error", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = init?.method ?? "GET";
          if (url.endsWith("/jobs") && method === "POST") {
            return Promise.reject(new Error("enqueue blew up"));
          }
          if (url.endsWith("/jobs") && method === "GET") {
            return Promise.resolve(jsonOk({ jobs: [] }));
          }
          if (url.includes("/finetune/adapter")) {
            return Promise.resolve(jsonOk(PIN_BASE));
          }
          return Promise.resolve(jsonOk({}));
        }),
    );
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-request-train-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-request-train-btn"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/enqueue blew up/i);
    });
  });

  it("no-ops promote when confirm checkbox is unchecked", async () => {
    const onPromote = vi.fn();
    stubFinetuneApis({ jobs: [COMPLETED_JOB], onPromote });
    renderFinetune();
    await waitFor(() => {
      expect(screen.getByTestId("finetune-view-eval-btn")).toBeEnabled();
    });
    fireEvent.click(screen.getByTestId("finetune-view-eval-btn"));
    await waitFor(() => {
      expect(screen.getByTestId("finetune-promote-btn")).toBeDisabled();
    });
    fireEvent.click(screen.getByTestId("finetune-promote-btn"));
    expect(onPromote).not.toHaveBeenCalled();
  });

  it("ignores late load errors after unmount", async () => {
    let rejectJobs: ((reason?: unknown) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/finetune/adapter")) {
          return Promise.resolve(jsonOk(PIN_BASE));
        }
        if (url.endsWith("/jobs")) {
          return new Promise((_resolve, reject) => {
            rejectJobs = reject;
          });
        }
        return Promise.resolve(jsonOk({}));
      }),
    );
    const { unmount } = renderFinetune();
    await waitFor(() => {
      expect(rejectJobs).toBeDefined();
    });
    unmount();
    rejectJobs?.(new Error("late failure"));
  });
});
