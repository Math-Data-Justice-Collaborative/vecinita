/**
 * UI E2E for #89 (F32): job info survives navigating to another admin tab.
 *
 * Regression context (same class as #53): job status used to live only in `JobForm`'s
 * component-local state on `/corpus`, so navigating away unmounted it and dropped the
 * running/failed job. The fix makes jobs server-sourced and adds a Job Management tab that
 * lists `GET /jobs`. This test starts an ingest job on the Corpus tab, navigates to the Jobs
 * tab, and asserts the job is still visible (re-fetched from the server) rather than lost.
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import App from "../App";

const JOB_ID = "11111111-1111-4111-8111-111111111111";

const COMPLETED_JOB = {
  job_id: JOB_ID,
  status: "completed",
  job_type: "ingest",
  urls: ["https://example.com/page"],
  error_code: null,
  error_message: null,
  created_at: "2026-06-26T10:00:00Z",
  updated_at: "2026-06-26T10:01:00Z",
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

function renderApp(initialRoute = "/corpus") {
  return renderWithProviders(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Job Management navigation persistence (#89)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("keeps a job created on Corpus visible after switching to the Jobs tab", async () => {
    const fetchMock = vi.fn(
      (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const url = urlOf(input);
        const method = (init?.method ?? "GET").toUpperCase();

        if (url.includes("/internal/v1/documents")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.includes("/jobs")) {
          if (method === "POST") {
            return Promise.resolve(
              jsonResponse({ job_id: JOB_ID, status: "pending" }),
            );
          }
          // GET /jobs/{id} (single, polled by JobForm) vs GET /jobs (the list).
          if (/\/jobs\/[^/?]+$/.test(url)) {
            return Promise.resolve(jsonResponse(COMPLETED_JOB));
          }
          return Promise.resolve(jsonResponse({ jobs: [COMPLETED_JOB] }));
        }
        return Promise.resolve(jsonResponse({}));
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    renderApp("/corpus");

    // Start an ingest job from the Corpus tab and wait for it to complete locally.
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });

    // Navigate to another tab — this unmounts the Corpus page (and JobForm state).
    fireEvent.click(screen.getByRole("link", { name: /jobs/i }));

    // The Job Management tab re-fetches from the server, so the job is NOT lost.
    await waitFor(() => {
      expect(screen.getByTestId("job-row")).toBeInTheDocument();
    });
    expect(screen.getByText(JOB_ID.slice(0, 8))).toBeInTheDocument();
    expect(screen.getByText(/Completed/)).toBeInTheDocument();

    const listCalls = fetchMock.mock.calls.filter(([input, init]) => {
      const url = urlOf(input);
      const method = (init?.method ?? "GET").toUpperCase();
      return method === "GET" && /\/jobs(\?|$)/.test(url);
    });
    expect(listCalls.length).toBeGreaterThan(0);
  });
});
