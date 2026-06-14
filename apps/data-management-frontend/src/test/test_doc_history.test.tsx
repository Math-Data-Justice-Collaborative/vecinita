import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DocumentHistory } from "@/components/DocumentHistory";

const MOCK_HISTORY_ITEMS = [
  {
    id: "evt-1",
    event_type: "document.created",
    entity_type: "document",
    entity_id: "doc-aaa",
    request_id: "req-1",
    created_at: "2026-05-26T10:00:00Z",
    payload: { title: "Housing Guide" },
  },
  {
    id: "evt-2",
    event_type: "document.tagged",
    entity_type: "document",
    entity_id: "doc-aaa",
    request_id: "req-2",
    created_at: "2026-05-26T11:00:00Z",
    payload: { tags_added: ["housing"] },
  },
];

function renderHistory() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <DocumentHistory documentId="doc-aaa" />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Document history timeline", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders timeline events for a document", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: MOCK_HISTORY_ITEMS,
        page: 1,
        page_size: 50,
        total_count: 2,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText("document.created")).toBeInTheDocument();
    });
    expect(screen.getByText("document.tagged")).toBeInTheDocument();
  });

  it("shows empty state when no history exists", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [], page: 1, page_size: 50, total_count: 0 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText(/no history/i)).toBeInTheDocument();
    });
  });

  it("shows empty state when fetch fails", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({ ok: false, status: 500 });
    vi.stubGlobal("fetch", fetchMock);

    renderHistory();

    await waitFor(() => {
      expect(
        screen.getByText(/no history for this document/i),
      ).toBeInTheDocument();
    });
  });
});
