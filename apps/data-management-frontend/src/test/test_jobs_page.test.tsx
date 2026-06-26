import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";

import { JobsPage } from "@/pages/JobsPage";

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
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

  it("lists jobs returned from the server", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MOCK_JOBS)));

    renderWithProviders(<JobsPage />);

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

    renderWithProviders(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByText(/no jobs yet/i)).toBeInTheDocument();
    });
  });

  it("shows an error when the jobs request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("boom", { status: 500 })),
    );

    renderWithProviders(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("shows a generic error for non-Error failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue("network down"));

    renderWithProviders(<JobsPage />);

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

    renderWithProviders(<JobsPage />);

    await waitFor(() => {
      expect(screen.getByTestId("job-row")).toBeInTheDocument();
    });
    expect(screen.getByText(/Ingest/)).toBeInTheDocument();
  });

  it("refetches jobs when the refresh button is clicked", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ jobs: [] }));
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<JobsPage />);

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

    renderWithProviders(<JobsPage />);
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

    const { unmount } = renderWithProviders(<JobsPage />);
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

    const { unmount } = renderWithProviders(<JobsPage />);
    unmount();
    reject?.(new Error("late failure"));
    await Promise.resolve();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
