import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { AuditPage } from "@/pages/AuditPage";

const MOCK_AUDIT = {
  items: [
    {
      id: "evt-1",
      event_type: "document.created",
      entity_type: "document",
      entity_id: "doc-aaa",
      request_id: "req-1",
      created_at: "2026-05-26T10:00:00Z",
      payload: { title: "Housing Guide", url: "https://example.com/housing" },
    },
    {
      id: "evt-2",
      event_type: "document.tagged",
      entity_type: "document",
      entity_id: "doc-bbb",
      request_id: "req-2",
      created_at: "2026-05-26T09:30:00Z",
      payload: { tags_added: ["legal"] },
    },
    {
      id: "evt-3",
      event_type: "document.deleted",
      entity_type: "document",
      entity_id: "doc-ccc",
      request_id: "req-3",
      created_at: "2026-05-26T09:00:00Z",
      payload: {},
    },
  ],
  total_count: 3,
  page: 1,
  page_size: 50,
};

function renderAudit() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <AuditPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Audit log page", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows loading state initially", () => {
    const fetchMock = vi.fn().mockReturnValue(new Promise(() => {}));
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders audit events table with event_type, entity, and timestamp", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_AUDIT,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();

    await waitFor(() => {
      expect(screen.getByText("document.created")).toBeInTheDocument();
    });
    expect(screen.getByText("document.tagged")).toBeInTheDocument();
    expect(screen.getByText("document.deleted")).toBeInTheDocument();
    expect(screen.getByText("doc-aaa")).toBeInTheDocument();
  });

  it("filters by event type", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_AUDIT })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...MOCK_AUDIT,
          items: [MOCK_AUDIT.items[0]],
          total_count: 1,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();

    await waitFor(() => {
      expect(screen.getByText("document.created")).toBeInTheDocument();
    });

    const filterInput = screen.getByTestId("filter-event-type");
    fireEvent.change(filterInput, { target: { value: "document.created" } });
    fireEvent.click(screen.getByTestId("apply-filters"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
  });

  it("expands payload detail when clicking a row", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_AUDIT,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();

    await waitFor(() => {
      expect(screen.getByText("document.created")).toBeInTheDocument();
    });

    const expandBtn = screen.getAllByTestId("expand-payload")[0];
    fireEvent.click(expandBtn);

    await waitFor(() => {
      expect(screen.getByText(/housing guide/i)).toBeInTheDocument();
    });
  });

  it("shows error on fetch failure", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
