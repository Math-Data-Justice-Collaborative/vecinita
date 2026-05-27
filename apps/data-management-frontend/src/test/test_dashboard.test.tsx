import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DashboardPage } from "@/pages/DashboardPage";

const MOCK_STATS = {
  total_documents: 42,
  total_chunks: 256,
  tag_distribution: [
    { tag: "housing", count: 15 },
    { tag: "legal", count: 10 },
  ],
  language_breakdown: [
    { language: "en", count: 30 },
    { language: "es", count: 12 },
  ],
  recent_activity: [
    { event_type: "document.created", entity_type: "document", entity_id: "abc", timestamp: "2026-05-26T10:00:00Z" },
    { event_type: "document.tagged", entity_type: "document", entity_id: "def", timestamp: "2026-05-26T09:00:00Z" },
  ],
  top_served: [
    { document_id: "aaa", title: "Top Doc", served_count: 100 },
  ],
};

function renderDashboard() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Dashboard page", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows loading state initially", () => {
    const fetchMock = vi.fn().mockReturnValue(new Promise(() => {}));
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders stat cards with fetched data", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_STATS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });
    expect(screen.getByText("256")).toBeInTheDocument();
  });

  it("renders top served documents widget", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_STATS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Top Doc")).toBeInTheDocument();
    });
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders recent activity feed", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_STATS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/document\.created/)).toBeInTheDocument();
    });
    expect(screen.getByText(/document\.tagged/)).toBeInTheDocument();
  });

  it("shows error state on fetch failure", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
