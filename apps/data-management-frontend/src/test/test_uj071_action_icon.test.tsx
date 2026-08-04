import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ACTION_ICON_MOTION_CLASS } from "vecinita-frontend-ui";

import { ThemeProvider } from "@/components/ThemeProvider";
import { HealthPage } from "@/pages/HealthPage";
import { renderWithProviders } from "./renderWithProviders";

/** api-contract shape (status + services object map, up/down). */
const MOCK_HEALTH = {
  status: "healthy" as const,
  services: {
    chat_rag_backend: { status: "up", latency_ms: 45, error: null },
    internal_write_api: { status: "up", latency_ms: 30, error: null },
    modal_embedding: {
      status: "down",
      latency_ms: null,
      error: "Connection refused",
    },
  },
  checked_at: "2026-05-26T10:00:00Z",
};

describe("UJ-071 / F66 ActionIcon wiring (admin Health)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("TC-221: refresh icon is aria-busy + spin while pending", async () => {
    let resolveRefresh: ((value: Response) => void) | undefined;
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => MOCK_HEALTH,
      })
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveRefresh = resolve;
          }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <HealthPage />
        </MemoryRouter>
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("chat_rag_backend")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      const icon = screen.getByTestId("health-refresh-icon");
      expect(icon).toHaveAttribute("aria-busy", "true");
      expect(icon.className).toContain(ACTION_ICON_MOTION_CLASS.spin);
    });

    resolveRefresh?.({
      ok: true,
      json: async () => MOCK_HEALTH,
    } as Response);

    await waitFor(() => {
      const icon = screen.getByTestId("health-refresh-icon");
      expect(icon).not.toHaveAttribute("aria-busy");
      expect(icon.className).not.toContain(ACTION_ICON_MOTION_CLASS.spin);
    });
  });
});
