import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DocumentHistory } from "@/components/DocumentHistory";

const MOCK_HISTORY = [
  {
    id: "evt-1",
    event_type: "document.created",
    entity_type: "document",
    entity_id: "doc-aaa",
    timestamp: "2026-05-26T10:00:00Z",
    payload: { title: "Housing Guide" },
  },
  {
    id: "evt-2",
    event_type: "document.tagged",
    entity_type: "document",
    entity_id: "doc-aaa",
    timestamp: "2026-05-26T11:00:00Z",
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
      json: async () => ({ events: MOCK_HISTORY }),
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
      json: async () => ({ events: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText(/no history/i)).toBeInTheDocument();
    });
  });
});
