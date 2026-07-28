import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { renderWithProviders } from "./renderWithProviders";
import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";

const PAGE_SIZE = 50;

function makeDocs(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    document_id: `doc-${String(i).padStart(3, "0")}`,
    url: `https://example.com/doc-${String(i)}`,
    title: `Doc ${String(i)}`,
    language: "en",
    tags: [],
  }));
}

function renderCorpus() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("BUG-2026-07-28 — Admin corpus list pagination (#112)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("requests a page from the API and renders pagination controls when total exceeds page size", async () => {
    const pageItems = makeDocs(PAGE_SIZE);
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: pageItems,
        page: 1,
        page_size: PAGE_SIZE,
        total: PAGE_SIZE + 10,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc 0")).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalled();
    const listCall = fetchMock.mock.calls.find((call) => {
      const url = String(call[0]);
      return url.includes("/internal/v1/documents");
    });
    expect(listCall).toBeDefined();
    const listUrl = String(listCall?.[0] ?? "");
    expect(listUrl).toMatch(/[?&]page=1\b/);
    expect(listUrl).toMatch(/[?&]page_size=\d+/);

    expect(screen.getByTestId("pagination-controls")).toBeInTheDocument();
    expect(screen.getByTestId("pagination-next")).toBeEnabled();

    fireEvent.click(screen.getByTestId("pagination-next"));

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((u) => /[?&]page=2\b/.test(u))).toBe(true);
    });
  });
});
