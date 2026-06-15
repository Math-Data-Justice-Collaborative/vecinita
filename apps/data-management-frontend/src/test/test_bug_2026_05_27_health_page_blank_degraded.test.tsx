/**
 * BUG-2026-05-27: Health page blank when /internal/v1/health/all returns api-contract shape.
 * @see docs/bug-reports/BUG-2026-05-27-health-page-blank-degraded.md
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { HealthPage } from "@/pages/HealthPage";

/** Production / api-contract response (object map, status field, up/down). */
const PRODUCTION_DEGRADED_HEALTH = {
  status: "degraded" as const,
  services: {
    database: { status: "up", latency_ms: 5, error: null },
    modal_embedding: { status: "down", latency_ms: null, error: "HTTP 404" },
    internal_write_api: { status: "up", latency_ms: 0, error: null },
  },
  checked_at: "2026-05-27T15:36:21.797972Z",
};

function renderHealth() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <HealthPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("BUG-2026-05-27 health page blank on degraded api-contract shape", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders service cards when API returns status + services object map", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => PRODUCTION_DEGRADED_HEALTH,
      }),
    );

    renderHealth();

    await waitFor(() => {
      expect(screen.getByTestId("overall-status")).toHaveTextContent(
        /degraded/i,
      );
    });
    expect(screen.getByText("modal_embedding")).toBeInTheDocument();
    expect(screen.getByText("HTTP 404")).toBeInTheDocument();
  });
});
