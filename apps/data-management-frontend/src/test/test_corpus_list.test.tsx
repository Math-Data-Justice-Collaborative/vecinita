import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";

const MOCK_DOCS = [
  {
    document_id: "aaa-111",
    url: "https://example.com/a",
    title: "Doc A",
    language: "en",
    tags: [{ slug: "housing", label: "Housing", source: "human" as const }],
  },
  {
    document_id: "bbb-222",
    url: "https://example.com/b",
    title: null,
    language: null,
    tags: [],
  },
];

function renderCorpus() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("CorpusList", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows empty corpus message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], page: 1, page_size: 50, total: 0 }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText(/no documents in corpus/i)).toBeInTheDocument();
    });
  });

  it("shows load error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new Error("load failed")),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("load failed");
    });
  });

  it("refreshes document list on Refresh click", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
  });

  it("deletes a document after confirmation", async () => {
    const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({ ok: true, status: 204 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [MOCK_DOCS[1]],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(confirmMock).toHaveBeenCalled();
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/documents/aaa-111"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  it("skips delete when confirmation is cancelled", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: MOCK_DOCS,
        page: 1,
        page_size: 50,
        total: MOCK_DOCS.length,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("opens DocumentAdmin when Manage tags is clicked", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ tags: [] }) });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /manage tags/i }));

    await waitFor(() => {
      expect(screen.getByLabelText("Document admin")).toBeInTheDocument();
    });
  });

  it("closes DocumentAdmin and returns to the corpus table", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ tags: [] }) });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /manage tags/i }));

    await waitFor(() => {
      expect(screen.getByLabelText("Document admin")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /close/i }));

    await waitFor(() => {
      expect(screen.queryByLabelText("Document admin")).not.toBeInTheDocument();
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });
  });

  it("deselects all when select-all is toggled off", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("select-all"));
    expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("select-all"));
    expect(screen.queryByTestId("bulk-toolbar")).not.toBeInTheDocument();
  });

  it("toggles an individual row selection on and off", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    const checkbox = within(row).getByRole("checkbox");

    fireEvent.click(checkbox);
    expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();

    fireEvent.click(checkbox);
    expect(screen.queryByTestId("bulk-toolbar")).not.toBeInTheDocument();
  });

  it("renders untitled fallback and em dash language", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("(untitled)")).toBeInTheDocument();
      expect(screen.getByText("—")).toBeInTheDocument();
    });
  });

  it("shows delete error message", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockRejectedValueOnce(new Error("delete exploded"));
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("delete exploded");
    });
  });

  it("shows generic delete error for non-Error failures", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            items: MOCK_DOCS,
            page: 1,
            page_size: 50,
            total: MOCK_DOCS.length,
          }),
        })
        .mockRejectedValueOnce("delete boom"),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Delete failed");
    });
  });

  it("uses the document url in the delete confirmation when title is missing", async () => {
    const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(false);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      }),
    );

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("(untitled)")).toBeInTheDocument();
    });

    const row = screen.getByText("(untitled)").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining("https://example.com/b"),
    );
  });

  it("shows generic load error for non-Error failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("bad corpus load"));

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to load corpus",
      );
    });
  });

  it("shows deleting label while delete is in progress", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockImplementationOnce(() => new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const row = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(
        within(row).getByRole("button", { name: /deleting/i }),
      ).toBeDisabled();
    });
  });

  it("ignores successful load after unmount", async () => {
    let resolveFetch: (value: Response) => void = () => undefined;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

    const { unmount } = renderCorpus();
    unmount();

    resolveFetch({
      ok: true,
      json: async () => ({
        items: MOCK_DOCS,
        page: 1,
        page_size: 50,
        total: MOCK_DOCS.length,
      }),
    } as Response);

    await new Promise((resolve) => {
      setTimeout(resolve, 50);
    });
  });

  it("ignores load error after unmount", async () => {
    let rejectFetch: (reason?: unknown) => void = () => undefined;
    const pendingFetch = new Promise<Response>((_, reject) => {
      rejectFetch = reject;
    });
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

    const { unmount } = renderCorpus();
    unmount();

    rejectFetch(new Error("load failed after unmount"));

    await new Promise((resolve) => {
      setTimeout(resolve, 50);
    });
  });

  it("loads corpus tree when Tree view is selected", async () => {
    const tree = {
      roots: [
        {
          id: "domain:tree.example.com",
          kind: "domain",
          label: "tree.example.com",
          counts: { documents: 1 },
          children: [
            {
              id: "doc-tree-1",
              kind: "document",
              label: "leaf.html",
              url: "https://tree.example.com/leaf.html",
              status: "completed",
            },
          ],
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => tree,
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(screen.getByText("tree.example.com")).toBeInTheDocument();
    });
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes("/corpus/tree"),
      ),
    ).toBe(true);
  });

  it("shows tree load error and refreshes tree view", async () => {
    const tree = {
      roots: [
        {
          id: "domain:refresh.example.com",
          kind: "domain",
          label: "refresh.example.com",
          children: [],
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockRejectedValueOnce(new Error("tree load failed"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => tree,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => tree,
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("tree load failed");
    });

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    await waitFor(() => {
      expect(screen.getByText("refresh.example.com")).toBeInTheDocument();
    });
  });

  it("shows generic tree load failure when reject is not an Error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockRejectedValueOnce("tree string failure");
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("switches from tree view back to flat list", async () => {
    const tree = {
      roots: [
        {
          id: "domain:switch.example.com",
          kind: "domain",
          label: "switch.example.com",
          children: [],
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => tree,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(screen.getByText("switch.example.com")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("corpus-view-flat"));
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });
  });

  it("refreshes tree after bulk delete completes in tree view", async () => {
    const treeWithDoc = {
      roots: [
        {
          id: "domain:bulk.example.com",
          kind: "domain",
          label: "bulk.example.com",
          children: [
            {
              id: "aaa-111",
              kind: "document",
              label: "Doc A",
              url: "https://example.com/a",
              status: "completed",
            },
          ],
        },
      ],
    };
    const treeAfter = {
      roots: [
        {
          id: "domain:bulk.example.com",
          kind: "domain",
          label: "bulk.example.com",
          children: [],
        },
      ],
    };
    const fetchMock = vi.fn().mockImplementation(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/corpus/tree")) {
        return {
          ok: true,
          json: async () =>
            fetchMock.mock.calls.filter(([u]) =>
              String(u).includes("/corpus/tree"),
            ).length > 1
              ? treeAfter
              : treeWithDoc,
        };
      }
      if (url.includes("/documents/bulk")) {
        return {
          ok: true,
          json: async () => ({
            successes: ["aaa-111"],
            failures: [],
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      };
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(screen.getByText("bulk.example.com")).toBeInTheDocument();
    });
    fireEvent.click(
      screen.getByRole("button", { name: /expand bulk\.example\.com/i }),
    );
    fireEvent.click(screen.getByRole("checkbox", { name: /select Doc A/i }));
    await waitFor(() => {
      expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("bulk-delete-btn"));
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => {
      const treeCalls = fetchMock.mock.calls.filter(([u]) =>
        String(u).includes("/corpus/tree"),
      );
      expect(treeCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("ignores tree load success after unmount", async () => {
    let resolveTree: (value: Response) => void = () => undefined;
    const pendingTree = new Promise<Response>((resolve) => {
      resolveTree = resolve;
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: MOCK_DOCS,
          page: 1,
          page_size: 50,
          total: MOCK_DOCS.length,
        }),
      })
      .mockReturnValueOnce(pendingTree);
    vi.stubGlobal("fetch", fetchMock);

    const { unmount } = renderCorpus();
    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("corpus-view-tree"));
    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
    unmount();

    resolveTree({
      ok: true,
      json: async () => ({ roots: [] }),
    } as Response);

    await new Promise((resolve) => {
      setTimeout(resolve, 50);
    });
  });

});
