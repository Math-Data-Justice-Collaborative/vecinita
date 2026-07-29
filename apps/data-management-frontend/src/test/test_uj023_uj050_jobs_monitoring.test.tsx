/**
 * EV-012 / #116 — Admin Jobs monitoring Vitest (T84.1).
 *
 * Covers TC-148 (SSE→4s poll fallback), TC-150 (retag document_id), TC-151
 * (status filter), and list→`/jobs/:id` detail navigation (UJ-050 / TC-146).
 */
import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { JobsPage } from "@/pages/JobsPage";
import { renderWithProviders } from "./renderWithProviders";

const INGEST_ID = "11111111-1111-4111-8111-111111111111";
const RETAG_ID = "22222222-2222-4222-8222-222222222222";
const RETAG_DOC_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

const MIXED_JOBS = {
  jobs: [
    {
      job_id: INGEST_ID,
      status: "completed",
      job_type: "ingest",
      urls: ["https://example.com/a"],
      document_id: null,
      error_code: null,
      error_message: null,
      created_at: "2026-07-28T10:00:00Z",
      updated_at: "2026-07-28T10:01:00Z",
    },
    {
      job_id: RETAG_ID,
      status: "failed",
      job_type: "retag",
      urls: [],
      document_id: RETAG_DOC_ID,
      error_code: "LlmTagClientError",
      error_message: "tag response is not valid JSON",
      created_at: "2026-07-28T09:00:00Z",
      updated_at: "2026-07-28T09:00:30Z",
    },
  ],
};

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function urlOf(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}

function hangingEventsResponse(): Promise<Response> {
  return new Promise(() => undefined);
}

function renderJobsRoutes(initialPath = "/jobs") {
  return renderWithProviders(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/jobs" element={<JobsPage />} />
        <Route
          path="/jobs/:jobId"
          element={<div data-testid="job-detail-route" />}
        />
        <Route
          path="/evaluation"
          element={<div data-testid="evaluation-route" />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("UJ-023 / UJ-050 Jobs monitoring (EV-012 T84.1)", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("filters the jobs list via GET /jobs?status= (TC-151)", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = urlOf(input);
      if (url.includes("/jobs/events")) {
        return hangingEventsResponse();
      }
      if (url.includes("status=failed")) {
        return Promise.resolve(
          jsonResponse({
            jobs: MIXED_JOBS.jobs.filter((j) => j.status === "failed"),
          }),
        );
      }
      return Promise.resolve(jsonResponse(MIXED_JOBS));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderJobsRoutes();

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(2);
    });

    const filter = screen.getByRole("combobox", { name: /status/i });
    fireEvent.change(filter, { target: { value: "failed" } });

    await waitFor(() => {
      const statusCalls = fetchMock.mock.calls.filter(([input]) =>
        urlOf(input).includes("/jobs?status=failed"),
      );
      expect(statusCalls.length).toBeGreaterThan(0);
    });

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(1);
    });
    expect(screen.getByText(RETAG_ID.slice(0, 8))).toBeInTheDocument();
    expect(screen.queryByText(INGEST_ID.slice(0, 8))).not.toBeInTheDocument();
  });

  it("shows retag document_id instead of an empty URLs cell (TC-150)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes("/jobs/events")) {
          return hangingEventsResponse();
        }
        return Promise.resolve(jsonResponse(MIXED_JOBS));
      }),
    );

    renderJobsRoutes();

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(2);
    });

    const retagRow = screen
      .getAllByTestId("job-row")
      .find((row) => within(row).queryByText(RETAG_ID.slice(0, 8)));
    expect(retagRow).toBeDefined();
    expect(within(retagRow!).getByText(RETAG_DOC_ID)).toBeInTheDocument();
  });

  it("navigates to /jobs/:id when a non-eval job row is clicked (UJ-050 / TC-146)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (urlOf(input).includes("/jobs/events")) {
          return hangingEventsResponse();
        }
        return Promise.resolve(jsonResponse(MIXED_JOBS));
      }),
    );

    renderJobsRoutes();

    await waitFor(() => {
      expect(screen.getByText(INGEST_ID.slice(0, 8))).toBeInTheDocument();
    });

    const ingestRow = screen
      .getAllByTestId("job-row")
      .find((row) => within(row).queryByText(INGEST_ID.slice(0, 8)));
    expect(ingestRow).toBeDefined();
    fireEvent.click(ingestRow!);

    await waitFor(() => {
      expect(screen.getByTestId("job-detail-route")).toBeInTheDocument();
    });
  });

  it("uses fetch SSE for job updates and falls back to 4s poll on SSE error (TC-148 / RD-173)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let rejectEvents: ((reason: unknown) => void) | undefined;
    let eventsCalls = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = urlOf(input);
      if (url.includes("/jobs/events")) {
        eventsCalls += 1;
        if (eventsCalls === 1) {
          return new Promise<Response>((_resolve, reject) => {
            rejectEvents = reject;
          });
        }
        return hangingEventsResponse();
      }
      return Promise.resolve(jsonResponse(MIXED_JOBS));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderJobsRoutes();

    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) =>
          urlOf(input).includes("/jobs/events"),
        ),
      ).toBe(true);
    });

    const listCallsBeforeError = fetchMock.mock.calls.filter(([input]) => {
      const url = urlOf(input);
      return /\/jobs(?:\?|$)/.test(url) && !url.includes("/jobs/events");
    }).length;

    rejectEvents?.(new Error("sse disconnected"));

    await waitFor(() => {
      expect(screen.getByTestId("jobs-poll-fallback")).toBeInTheDocument();
    });

    await vi.advanceTimersByTimeAsync(4500);

    const listCallsAfterError = fetchMock.mock.calls.filter(([input]) => {
      const url = urlOf(input);
      return /\/jobs(?:\?|$)/.test(url) && !url.includes("/jobs/events");
    }).length;
    expect(listCallsAfterError).toBeGreaterThan(listCallsBeforeError);

    await vi.advanceTimersByTimeAsync(2500);
    await waitFor(() => {
      expect(eventsCalls).toBeGreaterThan(1);
    });
  });
});
