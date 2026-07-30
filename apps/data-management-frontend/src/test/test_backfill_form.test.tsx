import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BackfillForm } from "../components/BackfillForm";
import { renderWithProviders } from "./renderWithProviders";
import {
  installAuthenticatedSupabaseMock,
  installViewerSupabaseMock,
} from "./supabaseMock";

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("BackfillForm (T87.5 / TP-S017-08)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "test-proxy-key");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("admin enqueues rescrape backfill by default", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "22222222-2222-4222-8222-222222222222",
          status: "pending",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("backfill-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("backfill-job-status")).toHaveTextContent(
        "pending",
      );
    });

    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.method).toBe("POST");
    expect(typeof init?.body).toBe("string");
    const body = JSON.parse(init?.body as string) as {
      urls: string[];
      options: {
        job_type: string;
        mode: string;
        backfill: boolean;
        backfill_source: string;
      };
    };
    expect(body.urls).toEqual([]);
    expect(body.options.job_type).toBe("rebuild");
    expect(body.options.mode).toBe("rescrape");
    expect(body.options.backfill).toBe(true);
    expect(body.options.backfill_source).toBe("rescrape");
  });

  it("requires ack before from_chunks backfill", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/backfill source/i), {
      target: { value: "from_chunks" },
    });
    fireEvent.click(screen.getByTestId("backfill-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/acknowledge/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("enqueues from_chunks when ack is checked", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "33333333-3333-4333-8333-333333333333",
          status: "pending",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/backfill source/i), {
      target: { value: "from_chunks" },
    });
    fireEvent.click(screen.getByTestId("backfill-ack"));
    fireEvent.click(screen.getByTestId("backfill-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("backfill-job-status")).toBeInTheDocument();
    });

    const requestInit = fetchMock.mock.calls[0]?.[1];
    expect(typeof requestInit?.body).toBe("string");
    const body = JSON.parse(requestInit?.body as string) as {
      options: {
        mode: string;
        backfill_source: string;
        ack_reconstruct_from_chunks: boolean;
      };
    };
    expect(body.options.mode).toBe("rechunk");
    expect(body.options.backfill_source).toBe("from_chunks");
    expect(body.options.ack_reconstruct_from_chunks).toBe(true);
  });

  it("viewer sees read-only notice instead of backfill controls", async () => {
    installViewerSupabaseMock();
    renderWithProviders(<BackfillForm />);

    expect(
      await screen.findByTestId("backfill-viewer-read-only"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("backfill-submit")).not.toBeInTheDocument();
  });

  it("clears from_chunks ack when switching back to rescrape", async () => {
    installAuthenticatedSupabaseMock();
    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });

    const source = screen.getByLabelText(/backfill source/i);
    fireEvent.change(source, { target: { value: "from_chunks" } });
    fireEvent.click(screen.getByTestId("backfill-ack"));
    expect(screen.getByTestId("backfill-ack")).toBeChecked();

    fireEvent.change(source, { target: { value: "rescrape" } });
    expect(screen.queryByTestId("backfill-ack")).not.toBeInTheDocument();

    fireEvent.change(source, { target: { value: "from_chunks" } });
    expect(screen.getByTestId("backfill-ack")).not.toBeChecked();

    fireEvent.change(source, { target: { value: "not-a-source" } });
    expect(source).toHaveValue("from_chunks");
  });

  it("shows API error message when backfill enqueue fails", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
        .mockRejectedValueOnce(new Error("backfill enqueue boom")),
    );

    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("backfill-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "backfill enqueue boom",
    );
  });

  it("shows fallback backfill error when reject is not an Error", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
        .mockRejectedValueOnce("not-an-error"),
    );

    renderWithProviders(<BackfillForm />);
    await waitFor(() => {
      expect(screen.getByTestId("backfill-submit")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("backfill-submit"));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
