/**
 * BUG-2026-05-27: Dashboard Invalid Date + empty Languages when stats/summary returns api-contract shape.
 * @see docs/bug-reports/BUG-2026-05-27-dashboard-invalid-date-languages.md
 */
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DashboardPage } from "@/pages/DashboardPage";

/** Production / api-contract response for GET /internal/v1/stats/summary. */
const API_CONTRACT_STATS = {
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
      entity_id: "8c0d2bef-f472-4674-8090-6c8050622035",
      created_at: "2026-05-27T21:41:55.326715Z",
      summary: "Ingested example.com/page",
    },
    {
      event_type: "document.deleted",
      entity_id: "4a435fec-f19f-40ea-a2dd-08417012ecb9",
      created_at: "2026-05-27T20:00:00.000000Z",
      summary: null,
    },
  ],
  top_served: [
    {
      document_id: "aaa",
      title: "Top Doc",
      served_count: 100,
      last_served_at: null,
    },
  ],
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

describe("BUG-2026-05-27 dashboard Invalid Date and empty Languages on api-contract shape", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows parsed timestamps and language count when API returns api-contract shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => API_CONTRACT_STATS,
      }),
    );

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/document\.created/)).toBeInTheDocument();
    });

    expect(screen.queryByText("Invalid Date")).not.toBeInTheDocument();
    expect(screen.getByText(/Ingested example\.com\/page/)).toBeInTheDocument();

    const languagesCard = screen.getByText("Languages").closest(".rounded-lg");
    expect(languagesCard).not.toBeNull();
    expect(
      within(languagesCard as HTMLElement).getByText("2"),
    ).toBeInTheDocument();
  });
});
