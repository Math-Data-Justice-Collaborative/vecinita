/**
 * EV-031 / F76 — corpus list parity badges (#245).
 */
import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CorpusList } from "@/components/CorpusList";
import { renderWithProviders } from "./renderWithProviders";

const EN_ONLY = {
  document_id: "en-only-1",
  url: "https://example.com/en",
  title: "English only",
  language: "en",
  paired_document_id: null,
};

const PAIRED_EN = {
  document_id: "paired-en",
  url: "https://example.com/paired",
  title: "Paired EN",
  language: "en",
  paired_document_id: "es-sibling-1",
};

describe("EV-031 corpus parity badges", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows Missing Spanish badge for unpaired EN documents", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [EN_ONLY],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      }),
    );

    renderWithProviders(<CorpusList />);

    await waitFor(() => {
      expect(screen.getByText("Missing Spanish")).toBeInTheDocument();
    });
  });

  it("hides parity badge when paired_document_id is present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [PAIRED_EN],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      }),
    );

    renderWithProviders(<CorpusList />);

    await waitFor(() => {
      expect(screen.getByText("Paired EN")).toBeInTheDocument();
    });
    expect(screen.queryByText("Missing Spanish")).not.toBeInTheDocument();
  });

  it("shows Missing English badge for unpaired ES documents", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [
            {
              document_id: "es-only-1",
              url: "https://example.com/es",
              title: "Solo español",
              language: "es",
              paired_document_id: null,
            },
          ],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      }),
    );

    renderWithProviders(<CorpusList />);

    await waitFor(() => {
      expect(screen.getByText("Missing English")).toBeInTheDocument();
    });
  });
});
