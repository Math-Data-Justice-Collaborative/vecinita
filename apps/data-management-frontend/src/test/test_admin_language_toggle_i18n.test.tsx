import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  detectBrowserLocale,
  LOCALE_STORAGE_KEY,
  readStoredLocale,
} from "vecinita-frontend-i18n";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

async function renderAdmin(initialRoute = "/dashboard") {
  return renderAppRoutesReady(initialRoute);
}

describe("TC-065: Admin language toggle (UJ-022, F31)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: query.includes("min-width: 768px"),
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/stats")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              total_documents: 0,
              total_chunks: 0,
              tag_distribution: [],
              language_breakdown: {},
              recent_activity: [],
              top_served: [],
            }),
          });
        }
        if (url.includes("/internal/v1/documents")) {
          return Promise.resolve({ ok: true, json: async () => [] });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders EN/ES language toggle in admin chrome on every route", async () => {
    for (const route of ["/dashboard", "/corpus", "/health", "/audit"]) {
      cleanup();
      await renderAdmin(route);
      expect(screen.getAllByTestId("language-toggle").length).toBeGreaterThan(
        0,
      );
      expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
    }
  });

  it("switches nav labels to Spanish when ES is selected", async () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    await renderAdmin();

    expect(
      screen.getByRole("link", { name: /^dashboard$/i }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: /^es$/i })[0]!);

    expect(screen.getByRole("link", { name: /^panel$/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /registro de auditoría/i }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("es");
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("es");
  });

  it("defaults to Spanish when browser language is neither English nor Spanish", () => {
    vi.stubGlobal("navigator", { language: "fr-FR" });
    expect(readStoredLocale()).toBeNull();
    expect(detectBrowserLocale()).toBe("es");
  });

  it("persists locale across remount (reload simulation)", async () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "es");
    const { unmount } = await renderAdmin();
    expect(screen.getByRole("link", { name: /^panel$/i })).toBeInTheDocument();
    unmount();
    await renderAdmin();
    expect(screen.getByRole("link", { name: /^panel$/i })).toBeInTheDocument();
  });
});
