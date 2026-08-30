/**
 * TC-303 / TC-304 / UJ-088 / F84 — Admin Monitoring page.
 * [Corpus: feature-list.md §F84] [Spec: docs/test-plan.md §TC-303]
 * [Spec: docs/acceptance-criteria.md §AC-MON1–AC-MON5]
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchInputUrl } from "./fetch-mock";
import { renderAppRoutesReady, useMediaQueryMock } from "./renderAppHelpers";

const SUMMARY_24H = {
  window: "24h",
  workloads: {
    ingest: { total: 40, succeeded: 36, failed: 4, success_rate: 0.9 },
    chat: {
      total: 120,
      succeeded: 118,
      failed: 2,
      success_rate: 0.983,
      no_context: 5,
    },
    embed: { total: 40, succeeded: 38, failed: 2, success_rate: 0.95 },
  },
  latency_ms: {
    chat: { p50: 1800, p95: 4200 },
    embed: { p50: 400, p95: 1200 },
  },
  top_error_codes: [
    { workload: "ingest", error_code: "EmbedClientError", count: 2 },
  ],
};

const SUMMARY_7D = {
  ...SUMMARY_24H,
  window: "7d",
  workloads: {
    ingest: { total: 200, succeeded: 190, failed: 10, success_rate: 0.95 },
    chat: {
      total: 800,
      succeeded: 790,
      failed: 10,
      success_rate: 0.9875,
      no_context: 20,
    },
    embed: { total: 200, succeeded: 195, failed: 5, success_rate: 0.975 },
  },
};

const TIMESERIES = {
  metric: "ingest_success_rate",
  window: "24h",
  buckets: [
    {
      t: "2026-08-29T00:00:00Z",
      success_rate: 0.9,
      total: 10,
      failed: 1,
    },
    {
      t: "2026-08-29T12:00:00Z",
      success_rate: 0.92,
      total: 12,
      failed: 1,
    },
  ],
};

function installMetricsFetch(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = fetchInputUrl(input);
      if (url.includes("/internal/v1/metrics/summary")) {
        const windowParam = new URL(url, "http://localhost").searchParams.get(
          "window",
        );
        const body = windowParam === "7d" ? SUMMARY_7D : SUMMARY_24H;
        return Promise.resolve({
          ok: true,
          json: async () => body,
        });
      }
      if (url.includes("/internal/v1/metrics/timeseries")) {
        return Promise.resolve({
          ok: true,
          json: async () => TIMESERIES,
        });
      }
      if (url.includes("/internal/v1/stats")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            total_documents: 0,
            total_chunks: 0,
            tag_distribution: [],
            language_breakdown: {},
            recent_activity: [],
            top_served: [],
          }),
        });
      }
      if (url.includes("/jobs")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ jobs: [] }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    }),
  );
}

describe("UJ-088 Monitoring page (TC-303, TC-304, F84)", () => {
  beforeEach(() => {
    useMediaQueryMock.mockReturnValue(true);
    installMetricsFetch();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows Monitoring nav link and renders summary cards for ingest/chat/embed", async () => {
    await renderAppRoutesReady("/monitoring");

    expect(
      screen.getByRole("link", { name: /monitoring/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("monitoring-page")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /monitoring/i, level: 2 }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-card-ingest")).toBeInTheDocument();
    });
    expect(screen.getByTestId("monitoring-card-chat")).toBeInTheDocument();
    expect(screen.getByTestId("monitoring-card-embed")).toBeInTheDocument();

    expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent(
      "90%",
    );
    expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent(
      "40",
    );
    expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent("4");
    expect(screen.getByTestId("monitoring-card-chat")).toHaveTextContent("98%");
    expect(screen.getByTestId("monitoring-card-embed")).toHaveTextContent(
      "95%",
    );
  });

  it("exposes window control and refetches summary for 7d", async () => {
    await renderAppRoutesReady("/monitoring");

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-card-ingest")).toBeInTheDocument();
    });

    const windowSelect = screen.getByTestId("monitoring-window");
    fireEvent.change(windowSelect, { target: { value: "7d" } });

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent(
        "95%",
      );
    });
    expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent(
      "200",
    );

    const fetchMock = vi.mocked(fetch);
    expect(
      fetchMock.mock.calls.some((call) => {
        const url = fetchInputUrl(call[0]);
        return url.includes("/metrics/summary") && url.includes("window=7d");
      }),
    ).toBe(true);
  });

  it("renders timeseries chart shell and top error codes without content leaks", async () => {
    await renderAppRoutesReady("/monitoring");

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-timeseries")).toBeInTheDocument();
    });
    const errors = screen.getByTestId("monitoring-errors");
    expect(errors).toBeInTheDocument();
    expect(errors).toHaveTextContent("EmbedClientError");
    expect(errors).toHaveTextContent("ingest");
    expect(errors).toHaveTextContent("2");

    const page = screen.getByTestId("monitoring-page");
    expect(page.textContent).not.toMatch(/question/i);
    expect(page.textContent).not.toMatch(/\banswer\b/i);
    expect(page.textContent).not.toMatch(/prompt/i);
    expect(page.textContent).not.toMatch(/What is housing/i);
  });

  it("links to Jobs for failed ingest drill-down (TC-304 / AC-MON3)", async () => {
    await renderAppRoutesReady("/monitoring");

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-view-jobs")).toBeInTheDocument();
    });
    const jobsLink = screen.getByTestId("monitoring-view-jobs");
    expect(jobsLink).toHaveAttribute("href", "/jobs");

    fireEvent.click(jobsLink);
    await waitFor(() => {
      expect(screen.getByTestId("jobs-page")).toBeInTheDocument();
    });
  });

  it("survives navigation away and back with server refetch (AC-MON2)", async () => {
    await renderAppRoutesReady("/monitoring");

    await waitFor(() => {
      expect(screen.getByTestId("monitoring-card-ingest")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("link", { name: /dashboard/i }));
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /dashboard/i, level: 2 }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("link", { name: /monitoring/i }));
    await waitFor(() => {
      expect(screen.getByTestId("monitoring-card-ingest")).toHaveTextContent(
        "90%",
      );
    });
    expect(screen.getByTestId("monitoring-timeseries")).toBeInTheDocument();
  });
});
