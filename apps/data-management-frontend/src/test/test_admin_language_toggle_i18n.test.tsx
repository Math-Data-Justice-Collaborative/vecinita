import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { LocaleProvider } from "vecinita-frontend-ui";
import {
  detectBrowserLocale,
  LOCALE_STORAGE_KEY,
  readStoredLocale,
} from "vecinita-frontend-i18n";

import { ThemeProvider } from "@/components/ThemeProvider";
import App from "../App";

function renderAdmin(initialRoute = "/dashboard") {
  return renderWithProviders(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>,
  );
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
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          total_documents: 0,
          total_chunks: 0,
          tag_distribution: [],
          language_breakdown: [],
          top_served: [],
          recent_activity: [],
        }),
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders EN/ES language toggle in admin chrome on every route", () => {
    for (const route of ["/dashboard", "/corpus", "/health", "/audit"]) {
      cleanup();
      renderAdmin(route);
      expect(screen.getAllByTestId("language-toggle").length).toBeGreaterThan(
        0,
      );
      expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
    }
  });

  it("switches nav labels to Spanish when ES is selected", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    renderAdmin();

    expect(
      screen.getByRole("link", { name: /^dashboard$/i }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: /^es$/i })[0]);

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

  it("persists locale across remount (reload simulation)", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "es");
    const { unmount } = renderAdmin();
    expect(screen.getByRole("link", { name: /^panel$/i })).toBeInTheDocument();
    unmount();
    renderAdmin();
    expect(screen.getByRole("link", { name: /^panel$/i })).toBeInTheDocument();
  });
});
