import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
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
    tags: [],
  },
  {
    document_id: "bbb-222",
    url: "https://example.com/b",
    title: "Doc B",
    language: "es",
    tags: [],
  },
  {
    document_id: "ccc-333",
    url: "https://example.com/c",
    title: "Doc C",
    language: "en",
    tags: [],
  },
];

function renderCorpus() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Bulk operations UI", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows checkboxes for each document row", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_DOCS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBeGreaterThanOrEqual(3);
  });

  it("shows select-all checkbox that toggles all rows", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_DOCS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const selectAll = screen.getByTestId("select-all");
    fireEvent.click(selectAll);

    const checkboxes = screen.getAllByRole("checkbox");
    const checked = checkboxes.filter(
      (cb) => cb.getAttribute("data-state") === "checked",
    );
    expect(checked.length).toBeGreaterThanOrEqual(3);
  });

  it("shows bulk action toolbar when documents are selected", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_DOCS,
    });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("bulk-toolbar")).not.toBeInTheDocument();

    const firstRow = screen.getByText("Doc A").closest("tr")!;
    const checkbox = within(firstRow).getByRole("checkbox");
    fireEvent.click(checkbox);

    expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();
    expect(screen.getByTestId("bulk-toolbar")).toHaveTextContent(/1 selected/i);
  });

  it("bulk delete opens confirmation dialog and calls API", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ successes: ["aaa-111"], failures: [] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => MOCK_DOCS.slice(1),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const firstRow = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(firstRow).getByRole("checkbox"));

    const deleteBtn = screen.getByTestId("bulk-delete-btn");
    fireEvent.click(deleteBtn);

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toBeInTheDocument();

    const confirmBtn = within(dialog).getByRole("button", { name: /confirm/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/internal/v1/documents/bulk"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  it("bulk tag opens dialog and applies tags", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ successes: ["aaa-111"], failures: [] }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const firstRow = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(firstRow).getByRole("checkbox"));
    fireEvent.click(screen.getByTestId("bulk-tag-btn"));

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText(/add tags/i), {
      target: { value: "legal" },
    });
    fireEvent.click(
      within(dialog).getByRole("button", { name: /apply tags/i }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/bulk/tags"),
        expect.objectContaining({ method: "PATCH" }),
      );
    });
  });

  it("bulk metadata opens dialog and updates fields", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ successes: ["aaa-111"], failures: [] }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    const firstRow = screen.getByText("Doc A").closest("tr")!;
    fireEvent.click(within(firstRow).getByRole("checkbox"));
    fireEvent.click(screen.getByTestId("bulk-metadata-btn"));

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText(/^title$/i), {
      target: { value: "Updated title" },
    });
    fireEvent.click(
      within(dialog).getByRole("button", { name: /update metadata/i }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/bulk/metadata"),
        expect.objectContaining({ method: "PATCH" }),
      );
    });
  });
});
