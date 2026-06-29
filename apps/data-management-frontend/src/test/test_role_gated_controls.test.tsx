import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { CorpusList } from "@/components/CorpusList";
import { JobForm } from "@/components/JobForm";
import { ThemeProvider } from "@/components/ThemeProvider";

import { renderWithProviders } from "./renderWithProviders";
import {
  installAuthenticatedSupabaseMock,
  installViewerSupabaseMock,
} from "./supabaseMock";

const MOCK_DOCS = [
  {
    document_id: "aaa-111",
    url: "https://example.com/a",
    title: "Doc A",
    language: "en",
    tags: [],
  },
];

function renderCorpusList() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <CorpusList />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

function renderJobForm() {
  return renderWithProviders(<JobForm />);
}

describe("UJ-029 role-gated write controls (TC-085)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("viewer cannot see corpus delete, manage-tags, or bulk selection controls", async () => {
    installViewerSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
    );

    renderCorpusList();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("button", { name: /delete/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /manage tags/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("select-all")).not.toBeInTheDocument();
  });

  it("viewer sees read-only notice instead of ingest form", async () => {
    installViewerSupabaseMock();

    renderJobForm();

    expect(
      await screen.findByTestId("viewer-read-only-notice"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /submit ingest/i }),
    ).not.toBeInTheDocument();
  });

  it("admin sees write controls on corpus list and ingest form", async () => {
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({ ok: true, json: async () => MOCK_DOCS }),
    );

    renderCorpusList();

    await waitFor(() => {
      expect(screen.getByText("Doc A")).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: /manage tags/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
    expect(screen.getByTestId("select-all")).toBeInTheDocument();

    cleanup();

    renderJobForm();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /submit ingest/i }),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("viewer-read-only-notice"),
    ).not.toBeInTheDocument();
  });
});
