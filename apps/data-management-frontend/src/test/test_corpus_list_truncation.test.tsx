import { cleanup, screen, waitFor, within } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";

const LONG_TITLE =
  "Extremely long corpus document title that must clip with ellipsis so the actions column stays on screen for operators";
const LONG_URL =
  "https://example.org/path/to/a/very/long/resource/name/that/would/otherwise/blow/out/the/table/layout";

const MANY_TAGS = Array.from({ length: 8 }, (_, i) => ({
  slug: `tag-${String(i)}`,
  label: `Tag ${String(i)}`,
  source: "human" as const,
}));

const LONG_DOC = {
  document_id: "long-001",
  url: LONG_URL,
  title: LONG_TITLE,
  language: "en",
  tags: MANY_TAGS,
};

function renderCorpus() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("CorpusList truncation (UJ-051 / TC-152–154)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("clips long title and URL with full text via title/aria-label; Actions remain", async () => {
    const cookieBefore = document.cookie;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [LONG_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByTestId("corpus-title-long-001")).toBeInTheDocument();
    });

    const title = screen.getByTestId("corpus-title-long-001");
    expect(title).toHaveAttribute("title", LONG_TITLE);
    expect(title).toHaveAttribute("aria-label", LONG_TITLE);
    expect(title).toHaveClass("truncate");

    const url = screen.getByTestId("corpus-url-long-001");
    expect(url).toHaveAttribute("href", LONG_URL);
    expect(url).toHaveAttribute("title", LONG_URL);
    expect(url).toHaveAttribute("aria-label", LONG_URL);

    const row = title.closest("tr");
    expect(row).not.toBeNull();
    expect(
      within(row as HTMLElement).getByRole("button", { name: /manage tags/i }),
    ).toBeInTheDocument();

    expect(screen.getByTestId("corpus-table-scroll")).toBeInTheDocument();
    expect(document.cookie).toBe(cookieBefore);
  });

  it("bounds tag chips with +N overflow", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [LONG_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(
        screen.getByTestId("corpus-tags-more-long-001"),
      ).toBeInTheDocument();
    });

    const more = screen.getByTestId("corpus-tags-more-long-001");
    expect(more).toHaveTextContent("+5");
    const overflowLabels = MANY_TAGS.slice(3)
      .map((t) => t.label)
      .join(", ");
    expect(more).toHaveAttribute("title", overflowLabels);
    expect(more).toHaveAttribute("aria-label", overflowLabels);
  });
});
