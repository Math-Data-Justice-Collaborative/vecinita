/**
 * T110.3 / TC-205–206 — Corpus tree expand/collapse, status/counts, bulk selection (F61).
 */
import { cleanup, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusTree } from "@/components/CorpusTree";
import type { TreeNode } from "@/api/types";
import { renderWithProviders } from "./renderWithProviders";

const MOCK_TREE: TreeNode[] = [
  {
    id: "domain:tree.example.com",
    kind: "domain",
    label: "tree.example.com",
    counts: { documents: 2 },
    children: [
      {
        id: "path:tree.example.com/guides",
        kind: "path",
        label: "guides",
        children: [
          {
            id: "doc-a",
            kind: "document",
            label: "a.html",
            url: "https://tree.example.com/guides/a.html",
            status: "completed",
            source_domain: "tree.example.com",
            source_path: "/guides",
          },
          {
            id: "doc-b",
            kind: "document",
            label: "b.html",
            url: "https://tree.example.com/guides/b.html",
            status: "failed",
            source_domain: "tree.example.com",
            source_path: "/guides",
          },
        ],
      },
    ],
  },
];

function renderTree(
  props: Partial<{
    selectedIds: Set<string>;
    onToggleSelect: (id: string) => void;
  }> = {},
) {
  const onToggleSelect = props.onToggleSelect ?? vi.fn();
  const selectedIds = props.selectedIds ?? new Set<string>();
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusTree
          roots={MOCK_TREE}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
        />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("CorpusTree", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("expands and collapses domain nodes and shows document counts (TC-205)", () => {
    renderTree();

    const domain = screen.getByRole("treeitem", {
      name: /tree\.example\.com/i,
    });
    expect(within(domain).getByText(/2/)).toBeInTheDocument();

    // Children hidden until expand
    expect(screen.queryByText("guides")).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /expand tree\.example\.com/i }),
    );
    expect(screen.getByText("guides")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /expand guides/i }));
    expect(screen.getByText("a.html")).toBeInTheDocument();
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
    expect(screen.getByText(/failed/i)).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /collapse tree\.example\.com/i }),
    );
    expect(screen.queryByText("a.html")).not.toBeInTheDocument();
  });

  it("toggles document selection for bulk actions (TC-206)", () => {
    const onToggleSelect = vi.fn();
    renderTree({ onToggleSelect });

    fireEvent.click(
      screen.getByRole("button", { name: /expand tree\.example\.com/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: /expand guides/i }));

    const checkboxA = screen.getByRole("checkbox", { name: /select a\.html/i });
    fireEvent.click(checkboxA);
    expect(onToggleSelect).toHaveBeenCalledWith("doc-a");
  });
});
