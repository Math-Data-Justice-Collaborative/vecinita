import { cleanup, screen, within } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";

function renderCorpusList() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Tag chips in corpus list", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders LLM tags with blue styling and human tags with green styling", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          document_id: "aaaa-1111",
          url: "https://example.com/page1",
          title: "Housing Guide",
          language: "en",
          tags: [
            { slug: "housing", label: "housing", source: "llm" },
            { slug: "legal", label: "legal", source: "human" },
          ],
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpusList();

    const housingBadge = await screen.findByTestId("tag-housing");
    expect(housingBadge).toBeInTheDocument();
    expect(housingBadge).toHaveTextContent("housing");
    expect(housingBadge.className).toMatch(/blue/);

    const legalBadge = screen.getByTestId("tag-legal");
    expect(legalBadge).toBeInTheDocument();
    expect(legalBadge).toHaveTextContent("legal");
    expect(legalBadge.className).toMatch(/green/);
  });

  it("renders documents without tags (no tag section)", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          document_id: "bbbb-2222",
          url: "https://example.com/page2",
          title: "No Tags Doc",
          language: "en",
          tags: [],
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpusList();

    await screen.findByText("No Tags Doc");
    expect(screen.queryAllByTestId(/^tag-/)).toHaveLength(0);
  });

  it("renders multiple documents with their respective tags", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          document_id: "cccc-3333",
          url: "https://example.com/page3",
          title: "Doc A",
          language: "en",
          tags: [{ slug: "alpha", label: "alpha", source: "llm" }],
        },
        {
          document_id: "dddd-4444",
          url: "https://example.com/page4",
          title: "Doc B",
          language: "es",
          tags: [{ slug: "beta", label: "beta", source: "human" }],
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpusList();

    const rowA = await screen.findByText("Doc A");
    const rowB = screen.getByText("Doc B");

    const containerA = rowA.closest("tr")!;
    const containerB = rowB.closest("tr")!;

    expect(within(containerA).getByTestId("tag-alpha")).toBeInTheDocument();
    expect(within(containerB).getByTestId("tag-beta")).toBeInTheDocument();
  });
});
