vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LOCALE_STORAGE_KEY } from "vecinita-frontend-i18n";

import { renderSignedInApp, waitForAdminNav } from "./authSessionHarness";

describe("BUG-2026-07-28 — Spanish sign-out-all overflows sidebar (#105)", () => {
  beforeEach(() => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "es");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: async () => ({
            total_documents: 0,
            total_chunks: 0,
            tag_distribution: [],
            language_breakdown: {},
            recent_activity: [],
            top_served: [],
          }),
        }),
      ),
    );
  });

  afterEach(() => {
    localStorage.clear();
    cleanup();
    vi.restoreAllMocks();
  });

  it("keeps sign-out-all label wrappable and full-width inside the sidebar footer", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    await waitFor(() => {
      expect(
        screen.getByTestId("admin-sign-out-all-devices"),
      ).toBeInTheDocument();
    });

    const button = screen.getByTestId("admin-sign-out-all-devices");
    expect(button).toHaveTextContent(
      /cerrar sesión en todos los dispositivos/i,
    );

    // Regression: long ES label must wrap within md:w-60 sidebar (issue #105).
    expect(button.className.split(/\s+/)).toContain("w-full");
    expect(button.className.split(/\s+/)).toContain("whitespace-normal");
    expect(button.className.split(/\s+/)).not.toContain("whitespace-nowrap");
  });
});
