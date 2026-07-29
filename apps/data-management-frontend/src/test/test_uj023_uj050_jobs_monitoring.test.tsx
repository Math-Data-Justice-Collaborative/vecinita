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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

type MockEventSourceHandler = ((ev: Event) => void) | null;

class MockEventSource {
  static instances: MockEventSource[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;

  readonly url: string;
  readyState = MockEventSource.CONNECTING;
  onopen: MockEventSourceHandler = null;
  onmessage: MockEventSourceHandler = null;
  onerror: MockEventSourceHandler = null;
  close = vi.fn(() => {
    this.readyState = MockEventSource.CLOSED;
  });

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
    this.readyState = MockEventSource.OPEN;
    queueMicrotask(() => {
      this.onopen?.(new Event("open"));
    });
  }

  addEventListener(
    type: string,
    listener: EventListenerOrEventListenerObject,
  ): void {
    const handler =
      typeof listener === "function"
        ? (listener as (ev: Event) => void)
        : (ev: Event) => {
            listener.handleEvent(ev);
          };
    if (type === "error") this.onerror = handler;
    if (type === "message") this.onmessage = handler;
    if (type === "open") this.onopen = handler;
    if (type === "job") {
      // Named SSE event: event: job
      this.onmessage = handler;
    }
  }

  removeEventListener(): void {
    /* no-op for tests */
  }

  dispatchError(): void {
    this.readyState = MockEventSource.CLOSED;
    this.onerror?.(new Event("error"));
  }
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
  beforeEach(() => {
    MockEventSource.instances = [];
    vi.stubGlobal("EventSource", MockEventSource);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("filters the jobs list via GET /jobs?status= (TC-151)", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = urlOf(input);
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
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MIXED_JOBS)));

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
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MIXED_JOBS)));

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

  it("uses SSE for job updates and falls back to 4s poll on SSE error (TC-148 / RD-173)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(MIXED_JOBS));
    vi.stubGlobal("fetch", fetchMock);

    renderJobsRoutes();

    await waitFor(() => {
      expect(MockEventSource.instances.length).toBeGreaterThan(0);
    });
    const sse = MockEventSource.instances[0];
    expect(sse).toBeDefined();
    expect(sse!.url).toMatch(/\/jobs\/events/);

    const listCallsBeforeError = fetchMock.mock.calls.filter(([input]) => {
      const url = urlOf(input);
      return url.includes("/jobs") && !url.includes("/jobs/events");
    }).length;

    sse!.dispatchError();

    await vi.advanceTimersByTimeAsync(4500);

    const listCallsAfterError = fetchMock.mock.calls.filter(([input]) => {
      const url = urlOf(input);
      return url.includes("/jobs") && !url.includes("/jobs/events");
    }).length;
    expect(listCallsAfterError).toBeGreaterThan(listCallsBeforeError);

    await waitFor(() => {
      expect(MockEventSource.instances.length).toBeGreaterThan(1);
    });
  });
});
