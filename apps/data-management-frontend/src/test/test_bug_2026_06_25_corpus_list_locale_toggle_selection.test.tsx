import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { useLocale } from "vecinita-frontend-ui";

import { renderWithProviders } from "./renderWithProviders";
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
];

function LocaleSwitcher() {
  const { setLocale } = useLocale();
  return (
    <button
      type="button"
      data-testid="switch-to-es"
      onClick={() => {
        setLocale("es");
      }}
    >
      switch
    </button>
  );
}

function renderCorpusWithSwitcher() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <LocaleSwitcher />
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("BUG-2026-06-25: CorpusList locale toggle preserves selection", () => {
  afterEach(() => {
    localStorage.clear();
    cleanup();
    vi.restoreAllMocks();
  });

  it("keeps bulk selection and does not refetch when the locale is switched", async () => {
    localStorage.setItem("vecinita.locale", "en");
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => MOCK_DOCS });
    vi.stubGlobal("fetch", fetchMock);

    renderCorpusWithSwitcher();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTestId("select-all"));
    expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("switch-to-es"));

    // Selection must survive the locale switch (bulk toolbar still shown)...
    await waitFor(() => {
      expect(document.documentElement.lang).toBe("es");
    });
    expect(screen.getByTestId("bulk-toolbar")).toBeInTheDocument();
    // ...and switching language must not re-run the corpus loader.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
