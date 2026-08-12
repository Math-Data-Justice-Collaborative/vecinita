/**
 * UJ-081 / T128.6 — DM freshness UI (stale list, enable, Refresh now).
 *
 * [Corpus: feature-list.md §F76]
 * [Corpus: user-journeys.md §UJ-081]
 * [Spec: docs/test-plan.md §TC-258 §TC-259]
 * [Spec: docs/acceptance-criteria.md §AC-FR3 §AC-FR4]
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { CorpusList } from "@/components/CorpusList";
import { DocumentAdmin } from "@/components/DocumentAdmin";
import { renderWithProviders } from "./renderWithProviders";
import { mockFetchUrl } from "./fetch-mock";

const STALE_DOC = {
  document_id: "doc-stale-1",
  url: "https://example.com/stale",
  title: "Stale Source",
  language: "en",
  tags: [],
  refresh_enabled: true,
  last_checked_at: "2026-06-01T00:00:00Z",
  stale: true,
};

function jsonOk(body: unknown) {
  return { ok: true, json: async () => body };
}

function renderCorpus() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("UJ-081 freshness UI (T128.6)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("TC-258: shows stale badge and last_checked on corpus list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        jsonOk({
          items: [STALE_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      ),
    );

    renderCorpus();

    await waitFor(() => {
      expect(
        screen.getByTestId(`corpus-stale-badge-${STALE_DOC.document_id}`),
      ).toHaveTextContent(/stale/i);
    });
    expect(
      screen.getByTestId(`corpus-last-checked-${STALE_DOC.document_id}`),
    ).toHaveTextContent(/2026-06-01/);
  });

  it("TC-258: stale-only filter requests listDocuments?stale=true", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk({
          items: [STALE_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      )
      .mockResolvedValueOnce(
        jsonOk({
          items: [STALE_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderCorpus();

    await waitFor(() => {
      expect(screen.getByTestId("corpus-stale-filter")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("corpus-stale-filter"));

    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
    const staleUrl = mockFetchUrl(fetchMock.mock.calls.length - 1);
    expect(staleUrl).toContain("stale=true");
  });

  it("TC-259: DocumentAdmin toggles refresh_enabled via PATCH", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonOk([]))
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(
        jsonOk({
          document_id: STALE_DOC.document_id,
          url: STALE_DOC.url,
          title: STALE_DOC.title,
          display_title: null,
          language: "en",
          refresh_enabled: false,
          last_checked_at: STALE_DOC.last_checked_at,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const onChanged = vi.fn();
    renderWithProviders(
      <ThemeProvider>
        <DocumentAdmin
          document={STALE_DOC}
          onClose={vi.fn()}
          onChanged={onChanged}
        />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("document-refresh-enabled-toggle"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("document-refresh-enabled-toggle"));

    await waitFor(() => {
      expect(onChanged).toHaveBeenCalled();
    });

    const patchCall = fetchMock.mock.calls.find(
      (call) => (call[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(patchCall).toBeDefined();
    const patchInit = patchCall?.[1] as RequestInit;
    expect(typeof patchInit.body).toBe("string");
    expect(JSON.parse(patchInit.body as string)).toEqual({
      refresh_enabled: false,
    });
    expect(screen.getByTestId("document-refresh-now-btn")).toBeDisabled();
  });

  it("TC-259: Refresh now POSTs /refresh and shows queued status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonOk([]))
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ job_id: "fresh-job-9" }));
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <ThemeProvider>
        <DocumentAdmin document={STALE_DOC} onClose={vi.fn()} />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("document-refresh-now-btn")).toBeEnabled();
    });

    fireEvent.click(screen.getByTestId("document-refresh-now-btn"));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/fresh-job-9/i);
    });

    const refreshCall = fetchMock.mock.calls.find((call) =>
      String(call[0]).includes("/refresh"),
    );
    expect(refreshCall).toBeDefined();
    expect((refreshCall?.[1] as RequestInit).method).toBe("POST");
  });
});
