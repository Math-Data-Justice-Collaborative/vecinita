import { cleanup, screen, waitFor } from "@testing-library/react";
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
      expect(screen.getAllByTestId("job-row")).toHaveLength(2);
    });
    expect(screen.getByText(/Completed/)).toBeInTheDocument();
    expect(screen.getByText(/Failed/)).toBeInTheDocument();
    expect(screen.getByText(/LlmTagClientError/)).toBeInTheDocument();
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
});
