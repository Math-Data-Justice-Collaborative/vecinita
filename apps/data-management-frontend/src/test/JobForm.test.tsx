import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { JobForm } from "../components/JobForm";

describe("JobForm", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("parses URLs and shows completed job status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: "11111111-1111-4111-8111-111111111111", status: "pending" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: "11111111-1111-4111-8111-111111111111",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    render(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page\n" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8001/jobs",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "Modal-Key": "test-proxy-key" }),
      }),
    );
  });

  it("shows validation error when no URLs entered", async () => {
    render(<JobForm />);
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/at least one url/i);
  });
});
