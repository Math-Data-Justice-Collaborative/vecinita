import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { JobForm } from "../components/JobForm";
import { installAuthenticatedSupabaseMock } from "./supabaseMock";

async function renderReadyJobForm(
  props?: React.ComponentProps<typeof JobForm>,
) {
  installAuthenticatedSupabaseMock();
  renderWithProviders(<JobForm {...props} />);
  await waitFor(() => {
    expect(
      screen.getByRole("button", { name: /submit ingest/i }),
    ).toBeInTheDocument();
  });
}

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("JobForm", () => {
  beforeEach(() => {
    installAuthenticatedSupabaseMock();
  });

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
    await renderReadyJobForm();
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
    await renderReadyJobForm();
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /at least one url/i,
    );
  });

  it("shows validation error for chunk size below minimum", async () => {
    await renderReadyJobForm();
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
    await renderReadyJobForm();
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
    await renderReadyJobForm();
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
    await renderReadyJobForm({ onJobUpdate });
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
    await renderReadyJobForm();
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
    await renderReadyJobForm();
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ingest failed");
  });

  it("surfaces the Error message when ingest creation throws an Error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new Error("create job exploded")),
    );
    await renderReadyJobForm();
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "create job exploded",
    );
  });

  it("posts additive crawl options when crawl is enabled (TC-203)", async () => {
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "66666666-6666-4666-8666-666666666666",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "66666666-6666-4666-8666-666666666666",
          status: "completed",
          urls: ["https://example.com/seed"],
          created_at: "2026-08-03T00:00:00Z",
          updated_at: "2026-08-03T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await renderReadyJobForm();

    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/seed" },
    });
    fireEvent.click(screen.getByLabelText(/crawl same-site/i));
    fireEvent.change(screen.getByLabelText(/max depth/i), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByLabelText(/max pages/i), {
      target: { value: "10" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    const init = fetchMock.mock.calls[0]?.[1];
    expect(typeof init?.body).toBe("string");
    const body = JSON.parse(init?.body as string) as {
      options?: {
        crawl?: boolean;
        max_depth?: number;
        max_pages?: number;
        crawl_scope?: string;
        chunk_size_tokens?: number;
      };
    };
    expect(body.options?.crawl).toBe(true);
    expect(body.options?.max_depth).toBe(1);
    expect(body.options?.max_pages).toBe(10);
    expect(body.options?.crawl_scope).toBe("same_domain");
    expect(body.options?.chunk_size_tokens).toBe(256);
  });

  it("shows validation error when crawl max depth is invalid", async () => {
    await renderReadyJobForm();
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/seed" },
    });
    fireEvent.click(screen.getByTestId("ingest-crawl"));
    fireEvent.change(screen.getByTestId("ingest-max-depth"), {
      target: { value: "-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /max depth must be 0 or greater/i,
    );
  });

  it("shows validation error when crawl max pages is below one", async () => {
    await renderReadyJobForm();
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/seed" },
    });
    fireEvent.click(screen.getByTestId("ingest-crawl"));
    fireEvent.change(screen.getByTestId("ingest-max-depth"), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByTestId("ingest-max-pages"), {
      target: { value: "0" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /max pages must be at least 1/i,
    );
  });

  it("omits crawl options when crawl is off (AC-SC7 single-URL)", async () => {
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "77777777-7777-4777-8777-777777777777",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "77777777-7777-4777-8777-777777777777",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-08-03T00:00:00Z",
          updated_at: "2026-08-03T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await renderReadyJobForm();

    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    const requestInit = fetchMock.mock.calls[0]?.[1];
    expect(typeof requestInit?.body).toBe("string");
    const body = JSON.parse(requestInit?.body as string) as {
      options?: { crawl?: boolean; chunk_size_tokens?: number };
    };
    expect(body.options?.crawl).toBeUndefined();
    expect(body.options?.chunk_size_tokens).toBe(256);
  });
});
