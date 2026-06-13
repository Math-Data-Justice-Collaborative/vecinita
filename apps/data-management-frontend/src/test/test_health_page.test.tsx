import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { HealthPage } from "@/pages/HealthPage";

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

function renderHealth() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <HealthPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Health page", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows loading state initially", () => {
    const fetchMock = vi.fn().mockReturnValue(new Promise(() => {}));
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders service status cards with healthy/unhealthy states", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_HEALTH,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();

    await waitFor(() => {
      expect(screen.getByText("chat_rag_backend")).toBeInTheDocument();
    });
    expect(screen.getByText("internal_write_api")).toBeInTheDocument();
    expect(screen.getByText("modal_embedding")).toBeInTheDocument();

    expect(screen.getByText("45 ms")).toBeInTheDocument();
    expect(screen.getByText("Connection refused")).toBeInTheDocument();
  });

  it("shows overall status indicator", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_HEALTH,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();

    await waitFor(() => {
      expect(screen.getByTestId("overall-status")).toHaveTextContent(
        /healthy/i,
      );
    });
  });

  it("refreshes on button click", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => MOCK_HEALTH,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...MOCK_HEALTH, status: "degraded" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();

    await waitFor(() => {
      expect(screen.getByText("chat_rag_backend")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      expect(screen.getByTestId("overall-status")).toHaveTextContent(
        /degraded/i,
      );
    });
  });

  it("shows error on fetch failure", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
