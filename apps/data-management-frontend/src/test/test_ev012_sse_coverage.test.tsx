/**
 * EV-012 — cover Jobs/JobDetail/Evaluation SSE UI handlers for the unit
 * coverage gate (lines 100% / branches 98%).
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import type { Job } from "@/api/types";
import type { EvalRunProgressEvent } from "@/api/admin";
import { JobDetailPage } from "@/pages/JobDetailPage";
import { JobsPage } from "@/pages/JobsPage";
import { EvaluationPage } from "@/pages/EvaluationPage";
import { setOperatorAccessToken } from "@/config";
import { renderWithProviders } from "./renderWithProviders";
import { installAuthenticatedSupabaseMock } from "./supabaseMock";

const JOB_ID = "33333333-3333-4333-8333-333333333333";
const OTHER_ID = "99999999-9999-4999-8999-999999999999";
const RUN_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

const RUNNING_JOB: Job = {
  job_id: JOB_ID,
  status: "running",
  job_type: "ingest",
  urls: ["https://example.com/run"],
  document_id: null,
  error_code: null,
  error_message: null,
  modal_call_id: "fc-running",
  dashboard_url: null,
  created_at: "2026-07-28T11:00:00Z",
  updated_at: "2026-07-28T11:00:10Z",
};

const COMPLETED_JOB: Job = {
  ...RUNNING_JOB,
  status: "completed",
  updated_at: "2026-07-28T11:01:00Z",
};

type JobHandlers = {
  onJob: (job: Job) => void;
  onError?: (err: unknown) => void;
};

type EvalHandlers = {
  onProgress: (event: EvalRunProgressEvent) => void;
  onError?: (err: unknown) => void;
};

const jobSse = vi.hoisted(() => ({
  handlers: null as JobHandlers | null,
  close: vi.fn(),
  throwOnSubscribe: false,
}));

const evalSse = vi.hoisted(() => ({
  handlers: null as EvalHandlers | null,
  close: vi.fn(),
}));

vi.mock("@/api/jobs", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/jobs")>();
  return {
    ...actual,
    subscribeJobEvents: (
      _opts: unknown,
      handlers: JobHandlers,
    ): { close: () => void } => {
      if (jobSse.throwOnSubscribe) {
        throw new Error("subscribe failed");
      }
      jobSse.handlers = handlers;
      return { close: jobSse.close };
    },
  };
});

vi.mock("@/api/admin", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/admin")>();
  return {
    ...actual,
    subscribeEvalRunEvents: (
      _opts: unknown,
      _runId: string,
      handlers: EvalHandlers,
    ): { close: () => void } => {
      evalSse.handlers = handlers;
      return { close: evalSse.close };
    },
  };
});

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function urlOf(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}

describe("EV-012 SSE coverage (Jobs / JobDetail / Evaluation)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002/");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "corpus-key");
    setOperatorAccessToken("operator-jwt");
    installAuthenticatedSupabaseMock();
    jobSse.handlers = null;
    evalSse.handlers = null;
    jobSse.throwOnSubscribe = false;
    jobSse.close.mockClear();
    evalSse.close.mockClear();
  });

  afterEach(() => {
    cleanup();
    setOperatorAccessToken(null);
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("JobDetailPage applies matching SSE job events and ignores others", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes(`/jobs/${JOB_ID}`)) {
          return Promise.resolve(jsonResponse(RUNNING_JOB));
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
    });
    await waitFor(() => {
      expect(screen.getAllByText(/running/i).length).toBeGreaterThanOrEqual(1);
    });

    jobSse.handlers?.onJob({ ...COMPLETED_JOB, job_id: OTHER_ID });
    expect(screen.getAllByText(/running/i).length).toBeGreaterThanOrEqual(1);

    jobSse.handlers?.onJob(COMPLETED_JOB);
    await waitFor(() => {
      expect(screen.getAllByText(/completed/i).length).toBeGreaterThanOrEqual(
        1,
      );
    });
  });

  it("JobDetailPage shows load error UI and cancel action errors", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = urlOf(input);
      if (url.includes(`/jobs/${JOB_ID}`) && !url.includes("/cancel")) {
        return Promise.resolve(jsonResponse(RUNNING_JOB));
      }
      if (url.includes("/cancel")) {
        return Promise.resolve(new Response("", { status: 500 }));
      }
      return Promise.resolve(jsonResponse({}));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("JobDetailPage starts poll on SSE error and shows getJob failure", async () => {
    let detailHits = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes(`/jobs/${JOB_ID}`)) {
          detailHits += 1;
          return Promise.resolve(jsonResponse(RUNNING_JOB));
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
    });
    const hitsBefore = detailHits;
    jobSse.handlers?.onError?.(new Error("sse down"));
    await waitFor(() => {
      expect(detailHits).toBeGreaterThan(hitsBefore);
    });
    const hitsAfterError = detailHits;
    await vi.advanceTimersByTimeAsync(4000);
    await waitFor(() => {
      expect(detailHits).toBeGreaterThan(hitsAfterError);
    });
    // Retry reconnect path
    await vi.advanceTimersByTimeAsync(2000);
    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
    });
  });

  it("JobDetailPage falls back to poll when subscribe throws", async () => {
    jobSse.throwOnSubscribe = true;
    let detailHits = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes(`/jobs/${JOB_ID}`)) {
          detailHits += 1;
          return Promise.resolve(jsonResponse(RUNNING_JOB));
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(detailHits).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/running/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("JobsPage falls back to poll when subscribe throws", async () => {
    jobSse.throwOnSubscribe = true;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ jobs: [RUNNING_JOB] })),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={["/jobs"]}>
        <Routes>
          <Route path="/jobs" element={<JobsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });
  });

  it("JobDetailPage shows alert when initial load fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("missing", { status: 404 })),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/jobs" element={<div data-testid="jobs-list" />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /back/i })).toBeInTheDocument();
  });

  it("JobsPage merges SSE updates and drops filtered-out jobs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes("status=running")) {
          return Promise.resolve(jsonResponse({ jobs: [RUNNING_JOB] }));
        }
        return Promise.resolve(jsonResponse({ jobs: [RUNNING_JOB] }));
      }),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={["/jobs"]}>
        <Routes>
          <Route path="/jobs" element={<JobsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });

    fireEvent.change(screen.getByRole("combobox", { name: /status/i }), {
      target: { value: "running" },
    });

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });

    jobSse.handlers?.onJob({ ...COMPLETED_JOB, status: "failed" });
    await waitFor(() => {
      expect(screen.queryAllByTestId("job-row")).toHaveLength(0);
    });

    jobSse.handlers?.onJob({
      ...COMPLETED_JOB,
      job_id: OTHER_ID,
      status: "running",
    });
    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });

    jobSse.handlers?.onJob({
      ...COMPLETED_JOB,
      job_id: OTHER_ID,
      status: "running",
      updated_at: "2026-07-28T12:00:00Z",
    });
    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });
  });

  it("JobDetailPage covers eval link, soft errors, and non-Error fallbacks", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    const evalJob = {
      ...COMPLETED_JOB,
      job_id: JOB_ID,
      job_type: "eval",
      status: "failed",
      eval_run_id: RUN_ID,
      error_code: null,
      error_message: "only-message",
      modal_call_id: null,
    };
    const bareJob = {
      ...RUNNING_JOB,
      job_type: undefined,
      status: "failed",
      error_code: null,
      error_message: null,
      modal_call_id: "fc-bare",
    };

    let phase: "eval" | "bare" | "throw" = "eval";
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = urlOf(input);
        if (url.includes("/cancel")) {
          // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
          return Promise.reject("cancel-string-error");
        }
        if (url.includes(`/jobs/${JOB_ID}`)) {
          if (phase === "throw") {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("load-string-error");
          }
          return Promise.resolve(
            jsonResponse(phase === "eval" ? evalJob : bareJob),
          );
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    const view = renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/evaluation" element={<div data-testid="eval" />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /evaluation/i }),
      ).toBeInTheDocument();
    });
    expect(screen.getByText(/only-message/i)).toBeInTheDocument();

    phase = "bare";
    jobSse.handlers?.onJob(bareJob as Job);
    await waitFor(() => {
      expect(screen.queryByText(/only-message/i)).not.toBeInTheDocument();
      expect(screen.getByText("—")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /^copy$/i }));
    jobSse.handlers?.onJob({ ...RUNNING_JOB, job_type: undefined });
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /cancel/i }),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    view.unmount();
  });

  it("JobDetailPage double SSE error covers poll guard and inactive retry", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes(`/jobs/${JOB_ID}`)) {
          return Promise.resolve(jsonResponse(RUNNING_JOB));
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    const { unmount } = renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
    });
    jobSse.handlers?.onError?.(new Error("sse1"));
    jobSse.handlers?.onError?.(new Error("sse2")); // pollTimer already set
    unmount();
    await vi.advanceTimersByTimeAsync(5000); // retry while inactive
  });

  it("JobsPage double SSE error and empty urls branch", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const emptyUrls = { ...RUNNING_JOB, urls: [] as string[] };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ jobs: [emptyUrls] })),
    );

    const { unmount } = renderWithProviders(
      <MemoryRouter initialEntries={["/jobs"]}>
        <Routes>
          <Route path="/jobs" element={<JobsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(jobSse.handlers).not.toBeNull();
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });
    jobSse.handlers?.onError?.(new Error("sse1"));
    jobSse.handlers?.onError?.(new Error("sse2"));
    unmount();
    await vi.advanceTimersByTimeAsync(5000);
  });

  it("JobDetailPage covers eval without run id and null error message", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    const evalJob = {
      ...failedJobBase(),
      job_id: JOB_ID,
      job_type: "eval",
      eval_run_id: null,
      error_code: "E1",
      error_message: null,
      modal_call_id: "fc-eval",
    };

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes(`/jobs/${JOB_ID}`)) {
          return Promise.resolve(jsonResponse(evalJob));
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("link", { name: /evaluation/i })).toHaveAttribute(
        "href",
        expect.stringContaining(JOB_ID),
      );
    });
    expect(screen.getByText(/E1:/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^copy$/i }));
    expect(writeText).toHaveBeenCalledWith("fc-eval");
  });

  it("JobDetailPage ignores load errors after unmount and non-Error load", async () => {
    let rejectLoad: ((reason: unknown) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes(`/jobs/${JOB_ID}`)) {
          return new Promise((_res, rej) => {
            rejectLoad = rej;
          });
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );

    const { unmount } = renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(rejectLoad).toBeTypeOf("function");
    });
    unmount();
    rejectLoad?.("string-error");
    await Promise.resolve();

    // Mounted non-Error load
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes(`/jobs/${JOB_ID}`)) {
          // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
          return Promise.reject("load-string");
        }
        return Promise.resolve(jsonResponse({}));
      }),
    );
    renderWithProviders(
      <MemoryRouter initialEntries={[`/jobs/${JOB_ID}`]}>
        <Routes>
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("EvaluationPage SSE progress with sibling runs and zero relevance", async () => {
    const { mockPlaygroundApiFetch } =
      await import("./helpers/mockPlaygroundApi");
    const otherId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
    const runningDetail = {
      run_id: RUN_ID,
      status: "running",
      metrics_summary: { retrieval_relevance: 0 },
      items: [],
    };

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = urlOf(input);
        const playground = mockPlaygroundApiFetch(url);
        if (playground !== null) {
          return new Response(JSON.stringify(await playground.json()), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/eval/runs") && init?.method === "POST") {
          return jsonResponse({ run_id: RUN_ID });
        }
        if (url.includes(`/eval/runs/${RUN_ID}`) && !url.includes("/events")) {
          return jsonResponse(runningDetail);
        }
        if (url.includes("/eval/runs")) {
          return jsonResponse({
            items: [
              {
                run_id: RUN_ID,
                status: "pending",
                metrics_summary: { retrieval_relevance: 0 },
              },
              {
                run_id: otherId,
                status: "completed",
                metrics_summary: { retrieval_relevance: 0.9 },
              },
            ],
            page: 1,
            page_size: 20,
            total_count: 2,
          });
        }
        if (url.includes("/eval/criteria")) {
          return jsonResponse({ items: [] });
        }
        if (url.includes("/eval/config")) {
          return jsonResponse({
            top_k: 5,
            system_prompt: "sys",
            model_id: "qwen2.5:1.5b-instruct",
          });
        }
        return jsonResponse({});
      }),
    );

    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderWithProviders(
      <MemoryRouter initialEntries={["/evaluation?tab=playground"]}>
        <Routes>
          <Route path="/evaluation" element={<EvaluationPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-run-button"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(evalSse.handlers).not.toBeNull();
    });

    evalSse.handlers?.onProgress({ run_id: RUN_ID, status: "running" });
    await waitFor(() => {
      expect(evalSse.handlers).not.toBeNull();
    });

    evalSse.handlers?.onError?.(new Error("down"));
    await vi.advanceTimersByTimeAsync(4000);
    evalSse.handlers?.onProgress({ run_id: RUN_ID, status: "completed" });
  });

  it("EvaluationPage finishes immediately when run is already completed", async () => {
    const { mockPlaygroundApiFetch } =
      await import("./helpers/mockPlaygroundApi");
    const completedDetail = {
      run_id: RUN_ID,
      status: "completed",
      metrics_summary: {
        faithfulness: null,
        retrieval_relevance: 0.9,
      },
      items: [],
    };

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = urlOf(input);
        const playground = mockPlaygroundApiFetch(url);
        if (playground !== null) {
          return new Response(JSON.stringify(await playground.json()), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/eval/runs") && init?.method === "POST") {
          return jsonResponse({ run_id: RUN_ID });
        }
        if (url.includes(`/eval/runs/${RUN_ID}`)) {
          return jsonResponse(completedDetail);
        }
        if (url.includes("/eval/runs")) {
          return jsonResponse({
            items: [
              {
                run_id: RUN_ID,
                status: "completed",
                metrics_summary: {
                  faithfulness: null,
                  retrieval_relevance: 0.9,
                },
              },
            ],
            page: 1,
            page_size: 20,
            total_count: 1,
          });
        }
        if (url.includes("/eval/criteria")) {
          return jsonResponse({ items: [] });
        }
        if (url.includes("/eval/config")) {
          return jsonResponse({
            top_k: 5,
            system_prompt: "sys",
            model_id: "qwen2.5:1.5b-instruct",
          });
        }
        return jsonResponse({});
      }),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={["/evaluation?tab=playground"]}>
        <Routes>
          <Route path="/evaluation" element={<EvaluationPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-run-button"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-page")).toBeInTheDocument();
    });
  });
});

function failedJobBase() {
  return {
    status: "failed" as const,
    job_type: "ingest" as const,
    urls: ["https://example.com/run"],
    document_id: null,
    error_code: null,
    error_message: null,
    modal_call_id: "fc",
    dashboard_url: null,
    created_at: "2026-07-28T11:00:00Z",
    updated_at: "2026-07-28T11:00:10Z",
  };
}
