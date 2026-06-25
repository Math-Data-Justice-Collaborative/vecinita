import { cleanup, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DashboardPage } from "@/pages/DashboardPage";

/** api-contract wire shape for GET /internal/v1/stats/summary */
const MOCK_STATS = {
  total_documents: 42,
  total_chunks: 256,
  tag_distribution: [
    { slug: "housing", label: "Housing", document_count: 15 },
    { slug: "legal", label: "Legal", document_count: 10 },
  ],
  language_breakdown: { en: 30, es: 12 },
  recent_activity: [
    {
      event_type: "document.created",
      entity_id: "abc",
      created_at: "2026-05-26T10:00:00Z",
      summary: "Created doc",
    },
    {
      event_type: "document.tagged",
      entity_id: "def",
      created_at: "2026-05-26T09:00:00Z",
      summary: null,
    },
  ],
  top_served: [{ document_id: "aaa", title: "Top Doc", served_count: 100 }],
};

function renderDashboard() {
  return renderWithProviders(
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
    expect(screen.getByText("Created doc")).toBeInTheDocument();
    expect(screen.getByText("document")).toBeInTheDocument();
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

  it("renders empty top served and recent activity states", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...MOCK_STATS,
        top_served: [],
        recent_activity: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/no serving data yet/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/no recent activity/i)).toBeInTheDocument();
  });

  it("uses document_id when top served title is null", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...MOCK_STATS,
        top_served: [{ document_id: "zzz", title: null, served_count: 3 }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("zzz")).toBeInTheDocument();
    });
  });

  it("shows generic dashboard error for non-Error failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("stats down"));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to load dashboard",
      );
    });
  });
});
