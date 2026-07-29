/**
 * EV-012 / #116 — Job detail admin CRUD Vitest (T84.2, TC-147 / RD-176).
 *
 * Admin sees cancel/retry/delete; viewer gets read-only detail (no mutate controls).
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { JobDetailPage } from "@/pages/JobDetailPage";
import { renderWithProviders } from "./renderWithProviders";
import {
  installAuthenticatedSupabaseMock,
  installViewerSupabaseMock,
} from "./supabaseMock";

const RUNNING_JOB_ID = "33333333-3333-4333-8333-333333333333";
const FAILED_JOB_ID = "44444444-4444-4444-8444-444444444444";
const COMPLETED_JOB_ID = "55555555-5555-4555-8555-555555555555";

const RUNNING_JOB = {
  job_id: RUNNING_JOB_ID,
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

const FAILED_JOB = {
  job_id: FAILED_JOB_ID,
  status: "failed",
  job_type: "retag",
  urls: [],
  document_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  error_code: "ScrapeError",
  error_message: "upstream timeout",
  modal_call_id: "fc-failed",
  dashboard_url: "https://modal.com/apps/vecinita/logs/fc-failed",
  created_at: "2026-07-28T10:00:00Z",
  updated_at: "2026-07-28T10:05:00Z",
};

const COMPLETED_JOB = {
  job_id: COMPLETED_JOB_ID,
  status: "completed",
  job_type: "ingest",
  urls: ["https://example.com/done"],
  document_id: null,
  error_code: null,
  error_message: null,
  modal_call_id: "fc-done",
  dashboard_url: null,
  created_at: "2026-07-28T09:00:00Z",
  updated_at: "2026-07-28T09:02:00Z",
};

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

function renderDetail(jobId: string) {
  return renderWithProviders(
    <MemoryRouter initialEntries={[`/jobs/${jobId}`]}>
      <Routes>
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        <Route path="/jobs" element={<div data-testid="jobs-list-route" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("UJ-050 job detail admin CRUD (T84.2 / TC-147)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("admin sees cancel on running jobs and can invoke cancel (TC-147)", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = urlOf(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/jobs/events")) {
        return new Promise(() => undefined);
      }
      if (method === "POST" && url.includes(`/jobs/${RUNNING_JOB_ID}/cancel`)) {
        return Promise.resolve(
          jsonResponse({ ...RUNNING_JOB, status: "cancelled" }),
        );
      }
      if (url.includes(`/jobs/${RUNNING_JOB_ID}`)) {
        return Promise.resolve(jsonResponse(RUNNING_JOB));
      }
      return Promise.resolve(jsonResponse({}));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDetail(RUNNING_JOB_ID);

    await waitFor(() => {
      expect(screen.getByTestId("job-detail")).toBeInTheDocument();
    });

    const cancel = screen.getByRole("button", { name: /cancel/i });
    fireEvent.click(cancel);

    await waitFor(() => {
      const cancelCalls = fetchMock.mock.calls.filter(([input, init]) => {
        const url = urlOf(input);
        const method = (init?.method ?? "GET").toUpperCase();
        return (
          method === "POST" && url.includes(`/jobs/${RUNNING_JOB_ID}/cancel`)
        );
      });
      expect(cancelCalls.length).toBe(1);
    });
  });

  it("admin sees retry on failed jobs and delete on terminal jobs (TC-147)", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = urlOf(input);
      const method = (init?.method ?? "GET").toUpperCase();
      if (url.includes("/jobs/events")) {
        return new Promise(() => undefined);
      }
      if (method === "POST" && url.includes(`/jobs/${FAILED_JOB_ID}/retry`)) {
        return Promise.resolve(
          jsonResponse({ job_id: "new-job", status: "pending" }),
        );
      }
      if (method === "DELETE" && url.includes(`/jobs/${FAILED_JOB_ID}`)) {
        return Promise.resolve(new Response(null, { status: 204 }));
      }
      if (url.includes(`/jobs/${FAILED_JOB_ID}`)) {
        return Promise.resolve(jsonResponse(FAILED_JOB));
      }
      return Promise.resolve(jsonResponse({}));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDetail(FAILED_JOB_ID);

    await waitFor(() => {
      expect(screen.getByTestId("job-detail")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /delete/i }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input, init]) => {
          const url = urlOf(input);
          const method = (init?.method ?? "GET").toUpperCase();
          return method === "DELETE" && url.includes(`/jobs/${FAILED_JOB_ID}`);
        }),
      ).toBe(true);
    });

    cleanup();
    renderDetail(FAILED_JOB_ID);
    await waitFor(() => {
      expect(screen.getByTestId("job-detail")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input, init]) => {
          const url = urlOf(input);
          const method = (init?.method ?? "GET").toUpperCase();
          return (
            method === "POST" && url.includes(`/jobs/${FAILED_JOB_ID}/retry`)
          );
        }),
      ).toBe(true);
    });
  });

  it("viewer detail is read-only — no cancel/retry/delete controls (TC-147)", async () => {
    installViewerSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes("/jobs/events")) {
          return new Promise(() => undefined);
        }
        return Promise.resolve(jsonResponse(COMPLETED_JOB));
      }),
    );

    renderDetail(COMPLETED_JOB_ID);

    await waitFor(() => {
      expect(screen.getByTestId("job-detail")).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("button", { name: /cancel/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /retry/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /delete/i }),
    ).not.toBeInTheDocument();
  });

  it("shows modal call id, copy, and dashboard link on failed jobs (TC-149 / RD-177)", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes("/jobs/events")) {
          return new Promise(() => undefined);
        }
        return Promise.resolve(jsonResponse(FAILED_JOB));
      }),
    );
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    renderDetail(FAILED_JOB_ID);

    await waitFor(() => {
      expect(screen.getByText("fc-failed")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /copy/i }));
    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith("fc-failed");
    });

    const link = screen.getByRole("link", { name: /modal|dashboard|logs/i });
    expect(link).toHaveAttribute(
      "href",
      "https://modal.com/apps/vecinita/logs/fc-failed",
    );
  });
});
