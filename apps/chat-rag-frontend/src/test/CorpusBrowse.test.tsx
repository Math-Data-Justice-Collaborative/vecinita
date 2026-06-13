import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as browse from "../api/browse";
import { CorpusBrowse } from "../components/CorpusBrowse";
import { renderWithLocale } from "./renderWithLocale";

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
  beforeEach(() => {
    localStorage.setItem("vecinita.locale", "en");
    vi.mocked(browse.fetchTags).mockResolvedValue({
      tags: [
        {
          slug: "housing",
          label: "Housing",
          language: "en",
          document_count: 1,
        },
      ],
    });
    vi.mocked(browse.fetchDocuments).mockResolvedValue({
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
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("TC-048: corpus row opens external source URL", async () => {
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);

    const link = await screen.findByTestId("corpus-source-link");
    expect(link).toHaveAttribute("href", "https://example.org/housing-rights");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders browse tag chips", async () => {
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    expect(
      await screen.findByRole("button", { name: "Housing" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("browse-tag-chips")).toBeInTheDocument();
  });

  it("shows localized Spanish error when tag fetch fails", async () => {
    localStorage.setItem("vecinita.locale", "es");
    vi.mocked(browse.fetchTags).mockRejectedValueOnce(
      new Error("Tags failed (500)"),
    );
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    expect(
      await screen.findByText("No se pudieron cargar las etiquetas"),
    ).toBeInTheDocument();
  });

  it("shows localized error when document fetch fails", async () => {
    vi.mocked(browse.fetchDocuments).mockRejectedValueOnce(
      new Error("Browse failed (500)"),
    );
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    expect(
      await screen.findByText(/failed to load documents/i),
    ).toBeInTheDocument();
  });

  it("filters tag chips to the active locale", async () => {
    vi.mocked(browse.fetchTags).mockResolvedValueOnce({
      tags: [
        {
          slug: "housing",
          label: "Housing",
          language: "en",
          document_count: 1,
        },
        {
          slug: "vivienda",
          label: "Vivienda",
          language: "es",
          document_count: 1,
        },
      ],
    });
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    expect(
      await screen.findByRole("button", { name: "Housing" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Vivienda" }),
    ).not.toBeInTheDocument();
  });

  it("toggles tag filters and refetches documents", async () => {
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    const chip = await screen.findByRole("button", { name: "Housing" });
    fireEvent.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "true");
    await screen.findByText(/housing rights overview/i);
    expect(browse.fetchDocuments).toHaveBeenCalledWith(
      expect.objectContaining({ tags: ["housing"] }),
    );
    fireEvent.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "false");
  });

  it("paginates, searches, and navigates home", async () => {
    const onNavigateHome = vi.fn();
    vi.mocked(browse.fetchDocuments).mockResolvedValue({
      items: [
        {
          document_id: "00000000-0000-0000-0000-000000000002",
          title: null,
          url: "https://example.org/untitled",
          language: "en",
          tags: [],
        },
      ],
      page: 1,
      page_size: 1,
      total: 2,
    });

    renderWithLocale(<CorpusBrowse onNavigateHome={onNavigateHome} />);
    expect(await screen.findByText("Untitled document")).toBeInTheDocument();
    expect(screen.getByText("No tags")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/search title or url/i), {
      target: { value: "pantry" },
    });
    fireEvent.submit(screen.getByRole("searchbox").closest("form")!);

    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    fireEvent.click(screen.getByRole("button", { name: /^previous$/i }));
    fireEvent.click(screen.getByRole("button", { name: /back to chat/i }));

    expect(onNavigateHome).toHaveBeenCalled();
    expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument();
  });

  it("ignores whitespace-only search queries", async () => {
    renderWithLocale(<CorpusBrowse onNavigateHome={() => undefined} />);
    await screen.findByTestId("corpus-list");

    fireEvent.change(screen.getByLabelText(/search title or url/i), {
      target: { value: "   " },
    });
    fireEvent.submit(screen.getByRole("searchbox").closest("form")!);

    expect(browse.fetchDocuments).toHaveBeenCalled();
    const lastParams = vi.mocked(browse.fetchDocuments).mock.calls.at(-1)?.[0];
    expect(lastParams?.q).toBeUndefined();
  });

  it("does not update state after unmount during document load", async () => {
    let resolveDocs: ((value: browse.DocumentBrowsePage) => void) | undefined;
    vi.mocked(browse.fetchDocuments).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveDocs = resolve;
        }),
    );

    const { unmount } = renderWithLocale(
      <CorpusBrowse onNavigateHome={() => undefined} />,
    );
    unmount();
    resolveDocs?.({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    });
  });

  it("does not set tag error after unmount when tag fetch fails", async () => {
    let rejectTags: ((reason: unknown) => void) | undefined;
    vi.mocked(browse.fetchTags).mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectTags = reject;
        }),
    );

    const { unmount } = renderWithLocale(
      <CorpusBrowse onNavigateHome={() => undefined} />,
    );
    unmount();
    rejectTags?.(new Error("Tags failed (500)"));
  });

  it("does not set document error after unmount when document fetch fails", async () => {
    let rejectDocs: ((reason: unknown) => void) | undefined;
    vi.mocked(browse.fetchDocuments).mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectDocs = reject;
        }),
    );

    const { unmount } = renderWithLocale(
      <CorpusBrowse onNavigateHome={() => undefined} />,
    );
    unmount();
    rejectDocs?.(new Error("Browse failed (500)"));
  });

  it("does not update tags after unmount during tag load", async () => {
    let resolveTags: ((value: { tags: browse.TagFacet[] }) => void) | undefined;
    vi.mocked(browse.fetchTags).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTags = resolve;
        }),
    );

    const { unmount } = renderWithLocale(
      <CorpusBrowse onNavigateHome={() => undefined} />,
    );
    unmount();
    resolveTags?.({ tags: [] });
  });
});

describe("Tag chips in chat", () => {
  afterEach(() => {
    cleanup();
  });

  it("loads tag filter chips from browse API", async () => {
    const { TagFilterChips } = await import("../components/TagFilterChips");
    const onToggle = vi.fn();
    render(
      <TagFilterChips
        tags={[
          {
            slug: "housing",
            label: "Housing",
            language: "en",
            document_count: 1,
          },
        ]}
        selected={[]}
        locale="en"
        onToggle={onToggle}
      />,
    );
    await fireEvent.click(
      screen.getByTestId("tag-filter-chips").querySelector("button")!,
    );
    expect(onToggle).toHaveBeenCalledWith("housing");
  });

  it("localizes tag filter aria-label for Spanish locale", async () => {
    const { TagFilterChips } = await import("../components/TagFilterChips");
    render(
      <TagFilterChips
        tags={[
          {
            slug: "vivienda",
            label: "Vivienda",
            language: "es",
            document_count: 1,
          },
        ]}
        selected={["vivienda"]}
        locale="es"
        onToggle={vi.fn()}
      />,
    );
    expect(screen.getByTestId("tag-filter-chips")).toHaveAttribute(
      "aria-label",
      "Filtrar por tema",
    );
    expect(screen.getByRole("button", { name: "Vivienda" })).toHaveClass(
      "active",
    );
  });
});
