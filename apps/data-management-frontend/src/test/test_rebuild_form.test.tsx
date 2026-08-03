/**
 * T89.5 — Vitest rebuild enqueue + promote controls (TC-167 / TC-169 / UJ-053 / UJ-054).
 * Red-phase: RebuildForm + RebuildPromoteForm land in T89.6.
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RebuildForm } from "../components/RebuildForm";
import { RebuildPromoteForm } from "../components/RebuildPromoteForm";
import { renderWithProviders } from "./renderWithProviders";
import {
  installAuthenticatedSupabaseMock,
  installViewerSupabaseMock,
} from "./supabaseMock";

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("RebuildForm (T89.5 / TC-167 / UJ-053)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "test-proxy-key");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("admin enqueues rebuild with mode, force, and dry_run (TC-167)", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          status: "pending",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RebuildForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("rebuild-mode"), {
      target: { value: "rechunk" },
    });
    fireEvent.click(screen.getByTestId("rebuild-force"));
    fireEvent.click(screen.getByTestId("rebuild-dry-run"));
    fireEvent.click(screen.getByTestId("rebuild-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("rebuild-job-status")).toHaveTextContent(
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
        force: boolean;
        dry_run: boolean;
      };
    };
    expect(body.urls).toEqual([]);
    expect(body.options.job_type).toBe("rebuild");
    expect(body.options.mode).toBe("rechunk");
    expect(body.options.force).toBe(true);
    expect(body.options.dry_run).toBe(true);
  });

  it("viewer sees read-only notice instead of rebuild controls", async () => {
    installViewerSupabaseMock();
    renderWithProviders(<RebuildForm />);

    expect(
      await screen.findByTestId("rebuild-viewer-read-only"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("rebuild-submit")).not.toBeInTheDocument();
  });

  it("accepts reembed and rescrape modes and ignores invalid mode values", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValue(
        jsonResponse({
          job_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
          status: "pending",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RebuildForm />);
    const mode = await screen.findByTestId("rebuild-mode");

    fireEvent.change(mode, { target: { value: "reembed" } });
    expect(mode).toHaveValue("reembed");
    fireEvent.change(mode, { target: { value: "rescrape" } });
    expect(mode).toHaveValue("rescrape");
    fireEvent.change(mode, { target: { value: "not-a-mode" } });
    expect(mode).toHaveValue("rescrape");

    fireEvent.click(screen.getByTestId("rebuild-submit"));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    const init = fetchMock.mock.calls[0]?.[1];
    const body = JSON.parse(init?.body as string) as {
      options: { mode: string };
    };
    expect(body.options.mode).toBe("rescrape");
  });

  it("shows API error message when rebuild enqueue fails", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<
          (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
        >()
        .mockRejectedValueOnce(new Error("rebuild enqueue boom")),
    );

    renderWithProviders(<RebuildForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-submit")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("rebuild-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "rebuild enqueue boom",
    );
  });

  it("shows fallback rebuild error when reject is not an Error", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<
          (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
        >()
        .mockRejectedValueOnce("not-an-error"),
    );

    renderWithProviders(<RebuildForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-submit")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("rebuild-submit"));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});

describe("RebuildPromoteForm (T89.5 / TC-169 / UJ-054)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "test-corpus-key");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("admin confirms and promotes a shadow rebuild_run_id (TC-169)", async () => {
    installAuthenticatedSupabaseMock();
    const runId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          promoted: true,
          rebuild_run_id: runId,
          chunks_promoted: 12,
          documents_promoted: 3,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RebuildPromoteForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("rebuild-promote-run-id"), {
      target: { value: runId },
    });
    fireEvent.click(screen.getByTestId("rebuild-promote-confirm"));
    fireEvent.click(screen.getByTestId("rebuild-promote-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-result")).toHaveTextContent(
        "12",
      );
    });

    const [url, init] = fetchMock.mock.calls[0] ?? [];
    const urlText =
      typeof url === "string"
        ? url
        : url instanceof URL
          ? url.href
          : url instanceof Request
            ? url.url
            : "";
    expect(urlText).toContain(`/internal/v1/rebuild/${runId}/promote`);
    expect(init?.method).toBe("POST");
  });

  it("requires confirm before promote API call", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RebuildPromoteForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("rebuild-promote-run-id"), {
      target: { value: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" },
    });
    fireEvent.click(screen.getByTestId("rebuild-promote-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/confirm/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("requires rebuild_run_id before promote API call", async () => {
    installAuthenticatedSupabaseMock();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<RebuildPromoteForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-submit")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("rebuild-promote-confirm"));
    fireEvent.click(screen.getByTestId("rebuild-promote-submit"));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows API error message when promote fails", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<
          (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
        >()
        .mockRejectedValueOnce(new Error("promote boom")),
    );

    renderWithProviders(<RebuildPromoteForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("rebuild-promote-run-id"), {
      target: { value: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" },
    });
    fireEvent.click(screen.getByTestId("rebuild-promote-confirm"));
    fireEvent.click(screen.getByTestId("rebuild-promote-submit"));

    expect(await screen.findByRole("alert")).toHaveTextContent("promote boom");
  });

  it("shows fallback promote error when reject is not an Error", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi
        .fn<
          (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
        >()
        .mockRejectedValueOnce("not-an-error"),
    );

    renderWithProviders(<RebuildPromoteForm />);
    await waitFor(() => {
      expect(screen.getByTestId("rebuild-promote-submit")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("rebuild-promote-run-id"), {
      target: { value: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" },
    });
    fireEvent.click(screen.getByTestId("rebuild-promote-confirm"));
    fireEvent.click(screen.getByTestId("rebuild-promote-submit"));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("viewer sees read-only notice instead of promote controls", async () => {
    installViewerSupabaseMock();
    renderWithProviders(<RebuildPromoteForm />);

    expect(
      await screen.findByTestId("rebuild-promote-viewer-read-only"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("rebuild-promote-submit"),
    ).not.toBeInTheDocument();
  });
});
