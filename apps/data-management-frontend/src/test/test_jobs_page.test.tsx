import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";

import { JobsPage } from "@/pages/JobsPage";

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function renderJobsPage(ui: ReactElement = <JobsPage />) {
  return renderWithProviders(
    <MemoryRouter initialEntries={["/jobs"]}>
      <Routes>
        <Route path="/jobs" element={ui} />
        <Route path="/evaluation" element={<div data-testid="evaluation-route" />} />
      </Routes>
    </MemoryRouter>,
  );
}

const MOCK_JOBS = {
  jobs: [
    {
      job_id: "11111111-1111-4111-8111-111111111111",
      status: "completed",
      job_type: "ingest",
      urls: ["https://example.com/a", "https://example.com/b"],
      error_code: null,
      error_message: null,
      created_at: "2026-06-26T10:00:00Z",
      updated_at: "2026-06-26T10:01:00Z",
    },
    {
      job_id: "22222222-2222-4222-8222-222222222222",
      status: "failed",
      job_type: "retag",
      urls: [],
      error_code: "LlmTagClientError",
      error_message: "tag response is not valid JSON",
      created_at: "2026-06-26T09:00:00Z",
      updated_at: "2026-06-26T09:00:30Z",
    },
    {
      job_id: "44444444-4444-4444-8444-444444444444",
      status: "failed",
      job_type: "ingest",
      urls: ["https://example.com/c"],
      error_code: "ScrapeError",
      error_message: null,
      created_at: "2026-06-26T08:30:00Z",
      updated_at: "2026-06-26T08:30:30Z",
    },
  ],
};

describe("JobsPage", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders eval job type and navigates to evaluation on row click (TC-124)", async () => {
    const EVAL_JOB_ID = "55555555-5555-4555-8555-555555555555";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          jobs: [
            {
              job_id: EVAL_JOB_ID,
              status: "running",
              job_type: "eval",
              urls: [],
              error_code: null,
              error_message: null,
              created_at: "2026-07-02T12:00:00Z",
              updated_at: "2026-07-02T12:00:05Z",
            },
          ],
        }),
      ),
    );

    renderJobsPage(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Eval/)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("job-row"));
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-route")).toBeInTheDocument();
    });
  });

  it("lists jobs returned from the server", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MOCK_JOBS)));

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("job-row")).toHaveLength(3);
    });
    expect(screen.getByText(/Completed/)).toBeInTheDocument();
    expect(screen.getAllByText(/Failed/).length).toBeGreaterThan(0);
    expect(screen.getByText(/LlmTagClientError/)).toBeInTheDocument();
    expect(screen.getByText(/ScrapeError/)).toBeInTheDocument();
  });

  it("shows empty state when there are no jobs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ jobs: [] })),
    );

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getByText(/no jobs yet/i)).toBeInTheDocument();
    });
  });

  it("shows an error when the jobs request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("boom", { status: 500 })),
    );

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("shows a generic error for non-Error failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue("network down"));

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /failed to load jobs/i,
      );
    });
  });

  it("defaults job type to ingest when job_type is absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          jobs: [
            {
              job_id: "33333333-3333-4333-8333-333333333333",
              status: "running",
              urls: ["https://example.com/x"],
              created_at: "2026-06-26T08:00:00Z",
              updated_at: "2026-06-26T08:00:10Z",
            },
          ],
        }),
      ),
    );

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getByTestId("job-row")).toBeInTheDocument();
    });
    expect(screen.getByText(/Ingest/)).toBeInTheDocument();
  });

  it("refetches jobs when the refresh button is clicked", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ jobs: [] }));
    vi.stubGlobal("fetch", fetchMock);

    renderJobsPage();

    await waitFor(() => {
      expect(screen.getByText(/no jobs yet/i)).toBeInTheDocument();
    });
    const callsBefore = fetchMock.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThan(callsBefore);
    });
  });

  it("polls for job updates on an interval", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ jobs: [] }));
    vi.stubGlobal("fetch", fetchMock);

    renderJobsPage();
    await vi.advanceTimersByTimeAsync(4500);

    expect(fetchMock.mock.calls.length).toBeGreaterThan(1);
    vi.useRealTimers();
  });

  it("ignores a resolved load after unmount", async () => {
    let resolve: ((value: Response) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise<Response>((res) => {
          resolve = res;
        }),
      ),
    );

    const { unmount } = renderJobsPage();
    unmount();
    resolve?.(jsonResponse({ jobs: [] }));
    await Promise.resolve();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("ignores a rejected load after unmount", async () => {
    let reject: ((reason: unknown) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise<Response>((_res, rej) => {
          reject = rej;
        }),
      ),
    );

    const { unmount } = renderJobsPage();
    unmount();
    reject?.(new Error("late failure"));
    await Promise.resolve();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
