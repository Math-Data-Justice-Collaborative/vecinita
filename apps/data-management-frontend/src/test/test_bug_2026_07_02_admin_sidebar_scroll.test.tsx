import { cleanup, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

describe("BUG-2026-07-02 — Admin sidebar stays on left while main content scrolls", () => {
  beforeEach(() => {
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
        return Promise.resolve({ ok: true, json: async () => [] });
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("locks layout to viewport height so only main scrolls and sidebar stays visible", async () => {
    await renderAppRoutesReady("/dashboard");

    const layout = screen.getByTestId("admin-layout");
    expect(layout).toHaveClass("h-screen");
    expect(layout).toHaveClass("overflow-hidden");

    const main = screen.getByTestId("admin-main");
    expect(main).toHaveClass("overflow-auto");
    expect(main).toHaveClass("min-h-0");

    const sidebar = screen.getByTestId("admin-sidebar");
    expect(sidebar).toHaveClass("md:h-screen");
    expect(sidebar).toHaveClass("md:shrink-0");
  });
});
