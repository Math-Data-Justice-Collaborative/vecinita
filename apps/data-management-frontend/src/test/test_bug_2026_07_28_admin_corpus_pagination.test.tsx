import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { renderWithProviders } from "./renderWithProviders";
import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";

const PAGE_SIZE = 50;
const TOTAL = PAGE_SIZE + 10;

function makeDocs(count: number, offset = 0) {
  return Array.from({ length: count }, (_, i) => {
    const n = offset + i;
    return {
      document_id: `doc-${String(n).padStart(3, "0")}`,
      url: `https://example.com/doc-${String(n)}`,
      title: `Doc ${String(n)}`,
      language: "en",
      tags: [],
    };
  });
}

function pageFromUrl(url: string): number {
  const match = /[?&]page=(\d+)/.exec(url);
  return match ? Number(match[1]) : 1;
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
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo) => {
      const url = String(input);
      const page = pageFromUrl(url);
      const items =
        page === 1
          ? makeDocs(PAGE_SIZE, 0)
          : makeDocs(TOTAL - PAGE_SIZE, PAGE_SIZE);
      return Promise.resolve({
        ok: true,
        json: async () => ({
          items,
          page,
          page_size: PAGE_SIZE,
          total: TOTAL,
        }),
      });
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
      expect(screen.getByText(`Doc ${String(PAGE_SIZE)}`)).toBeInTheDocument();
    });
    expect(screen.getByTestId("pagination-previous")).toBeEnabled();

    fireEvent.click(screen.getByTestId("pagination-previous"));

    await waitFor(() => {
      expect(screen.getByText("Doc 0")).toBeInTheDocument();
    });
    const page1Calls = fetchMock.mock.calls.filter((call) =>
      /[?&]page=1\b/.test(String(call[0])),
    );
    // Initial load + return from page 2
    expect(page1Calls.length).toBeGreaterThanOrEqual(2);
  });
});
