import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { HealthPage } from "@/pages/HealthPage";

const MOCK_HEALTH = {
  overall: "healthy" as const,
  services: [
    { name: "chat-rag-backend", status: "healthy", latency_ms: 45, error: null },
    { name: "internal-write-api", status: "healthy", latency_ms: 30, error: null },
    { name: "modal-embedding", status: "unhealthy", latency_ms: null, error: "Connection refused" },
  ],
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
      expect(screen.getByText("chat-rag-backend")).toBeInTheDocument();
    });
    expect(screen.getByText("internal-write-api")).toBeInTheDocument();
    expect(screen.getByText("modal-embedding")).toBeInTheDocument();

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
      expect(screen.getByTestId("overall-status")).toHaveTextContent(/healthy/i);
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
        json: async () => ({ ...MOCK_HEALTH, overall: "degraded" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderHealth();

    await waitFor(() => {
      expect(screen.getByText("chat-rag-backend")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      expect(screen.getByTestId("overall-status")).toHaveTextContent(/degraded/i);
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
