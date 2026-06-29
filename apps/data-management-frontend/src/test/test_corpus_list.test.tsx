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
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => [] }),
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS });
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
      .mockResolvedValueOnce({ ok: true, status: 204 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [MOCK_DOCS[1]],
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
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS });
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
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
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
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
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
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
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
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
        .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
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
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
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
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
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
      json: async () => MOCK_DOCS,
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
});
