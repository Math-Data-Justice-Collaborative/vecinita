import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady, useMediaQueryMock } from "./renderAppHelpers";

async function renderApp(initialRoute = "/dashboard") {
  return renderAppRoutesReady(initialRoute);
}

const STATS_BODY = {
  total_documents: 0,
  total_chunks: 0,
  tag_distribution: [],
  language_breakdown: {},
  recent_activity: [],
  top_served: [],
};

describe("Admin navigation", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/internal/v1/stats")) {
          return Promise.resolve({
            ok: true,
            json: async () => STATS_BODY,
          });
        }
        if (url.includes("/internal/v1/documents")) {
          return Promise.resolve({ ok: true, json: async () => [] });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders sidebar with all navigation links", async () => {
    await renderApp();

    const nav = screen.getByTestId("admin-nav");
    expect(nav).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: /dashboard/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /corpus/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /jobs/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /health/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /audit log/i }),
    ).toBeInTheDocument();
  });

  it("navigates to corpus page when clicking Corpus link", async () => {
    await renderApp();

    fireEvent.click(screen.getByRole("link", { name: /corpus/i }));
    expect(
      screen.getByText(/ingest urls and manage documents/i),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/no documents in corpus/i)).toBeInTheDocument();
    });
  });

  it("navigates to health page", async () => {
    await renderApp();

    fireEvent.click(screen.getByRole("link", { name: /health/i }));
    expect(
      screen.getByRole("heading", { name: /health/i, level: 2 }),
    ).toBeInTheDocument();
  });

  it("navigates to audit log page", async () => {
    await renderApp();

    fireEvent.click(screen.getByRole("link", { name: /audit log/i }));
    expect(screen.getByText(/event history/i)).toBeInTheDocument();
  });

  it("redirects unknown routes to /dashboard", async () => {
    await renderApp("/unknown-route");

    expect(screen.getByText(/overview of your corpus/i)).toBeInTheDocument();
  });

  it("theme toggle button exists and is clickable", async () => {
    await renderApp();

    const toggles = screen.getAllByTestId("theme-toggle");
    expect(toggles.length).toBeGreaterThan(0);
    fireEvent.click(toggles[0]);
  });

  it("opens mobile navigation sheet", async () => {
    useMediaQueryMock.mockReturnValue(false);
    await renderApp();

    fireEvent.click(screen.getByRole("button", { name: /open navigation/i }));
    const sheetTitle = await screen.findAllByText("Vecinita");
    expect(sheetTitle.length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("link", { name: /corpus/i }));
    expect(
      screen.getByText(/ingest urls and manage documents/i),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/no documents in corpus/i)).toBeInTheDocument();
    });
  });
});
