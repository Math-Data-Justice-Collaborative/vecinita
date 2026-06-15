import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";

import { JobForm } from "../components/JobForm";

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("JobForm", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("parses URLs and shows completed job status", async () => {
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "11111111-1111-4111-8111-111111111111",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "11111111-1111-4111-8111-111111111111",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page\n" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.method).toBe("POST");
    const headers = new Headers(init?.headers);
    expect(headers.get("X-Vecinita-Proxy-Key")).toBe("test-proxy-key");
  });

  it("shows validation error when no URLs entered", async () => {
    renderWithProviders(<JobForm />);
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /at least one url/i,
    );
  });

  it("shows validation error for chunk size below minimum", async () => {
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.change(screen.getByLabelText(/chunk size/i), {
      target: { value: "not-a-number" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/at least 64/i);
  });

  it("shows failed job error details", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "22222222-2222-4222-8222-222222222222",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "22222222-2222-4222-8222-222222222222",
          status: "failed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
          error_code: "SCRAPE_ERROR",
          error_message: "Timeout",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await vi.runAllTimersAsync();

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("failed");
    });
    expect(screen.getByText(/SCRAPE_ERROR/)).toBeInTheDocument();

    vi.useRealTimers();
  });

  it("polls through running status before completion", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "44444444-4444-4444-8444-444444444444",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "44444444-4444-4444-8444-444444444444",
          status: "running",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "44444444-4444-4444-8444-444444444444",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:02Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await vi.runAllTimersAsync();

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);

    vi.useRealTimers();
  });

  it("invokes onJobUpdate callback during polling", async () => {
    const onJobUpdate = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "33333333-3333-4333-8333-333333333333",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "33333333-3333-4333-8333-333333333333",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<JobForm onJobUpdate={onJobUpdate} />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(onJobUpdate).toHaveBeenCalled();
    });
  });

  it("completes ingest without optional onJobUpdate callback", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "55555555-5555-4555-8555-555555555555",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "55555555-5555-4555-8555-555555555555",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
  });

  it("shows generic ingest error for non-Error failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("ingest down"));
    renderWithProviders(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ingest failed");
  });
});
