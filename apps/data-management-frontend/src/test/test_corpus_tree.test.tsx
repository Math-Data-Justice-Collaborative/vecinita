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

  it("shows empty-tree message when roots are empty", () => {
    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <CorpusTree
            roots={[]}
            selectedIds={new Set()}
            onToggleSelect={vi.fn()}
          />
        </MemoryRouter>
      </ThemeProvider>,
    );
    expect(
      screen.getByText(/no documents in corpus tree/i),
    ).toBeInTheDocument();
  });

  it("renders childless domain without expand control", () => {
    const roots: TreeNode[] = [
      {
        id: "domain:lonely.example.com",
        kind: "domain",
        label: "lonely.example.com",
        children: [],
      },
    ];
    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <CorpusTree
            roots={roots}
            selectedIds={new Set()}
            onToggleSelect={vi.fn()}
          />
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(screen.getByText("lonely.example.com")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /expand lonely\.example\.com/i }),
    ).not.toBeInTheDocument();
  });

  it("renders document nodes without status or url badges", () => {
    const roots: TreeNode[] = [
      {
        id: "domain:bare.example.com",
        kind: "domain",
        label: "bare.example.com",
        children: [
          {
            id: "doc-bare",
            kind: "document",
            label: "bare.html",
          },
        ],
      },
    ];
    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <CorpusTree
            roots={roots}
            selectedIds={new Set()}
            onToggleSelect={vi.fn()}
          />
        </MemoryRouter>
      </ThemeProvider>,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /expand bare\.example\.com/i }),
    );
    expect(screen.getByText("bare.html")).toBeInTheDocument();
    expect(
      screen.queryByText(/completed|failed|pending/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/https?:\/\//i)).not.toBeInTheDocument();
  });
});
