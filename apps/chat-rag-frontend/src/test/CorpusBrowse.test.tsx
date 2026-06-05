import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CorpusBrowse } from "../components/CorpusBrowse";

vi.mock("../api/browse", () => ({
  fetchTags: vi.fn(async () => ({
    tags: [
      { slug: "housing", label: "Housing", language: "en", document_count: 1 },
    ],
  })),
  fetchDocuments: vi.fn(async () => ({
    items: [
      {
        document_id: "00000000-0000-0000-0000-000000000001",
        title: "Housing Rights Overview",
        url: "https://example.org/housing-rights",
        language: "en",
        tags: [{ slug: "housing", label: "Housing" }],
      },
    ],
    page: 1,
    page_size: 20,
    total: 1,
  })),
}));

describe("CorpusBrowse", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("TC-048: corpus row opens external source URL", async () => {
    render(<CorpusBrowse onNavigateHome={() => undefined} />);

    const link = await screen.findByTestId("corpus-source-link");
    expect(link).toHaveAttribute("href", "https://example.org/housing-rights");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders browse tag chips", async () => {
    render(<CorpusBrowse onNavigateHome={() => undefined} />);
    expect(await screen.findByRole("button", { name: "Housing" })).toBeInTheDocument();
    expect(screen.getByTestId("browse-tag-chips")).toBeInTheDocument();
  });
});

describe("Tag chips in chat", () => {
  it("loads tag filter chips from browse API", async () => {
    const { TagFilterChips } = await import("../components/TagFilterChips");
    const onToggle = vi.fn();
    render(
      <TagFilterChips
        tags={[{ slug: "housing", label: "Housing", language: "en", document_count: 1 }]}
        selected={[]}
        locale="en"
        onToggle={onToggle}
      />,
    );
    await fireEvent.click(screen.getByTestId("tag-filter-chips").querySelector("button")!);
    expect(onToggle).toHaveBeenCalledWith("housing");
  });
});
