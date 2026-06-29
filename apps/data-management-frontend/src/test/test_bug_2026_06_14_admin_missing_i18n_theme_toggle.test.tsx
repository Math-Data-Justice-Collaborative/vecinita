import { cleanup, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

async function renderAdmin(route = "/dashboard") {
  return renderAppRoutesReady(route);
}

describe("BUG-2026-06-14 — Admin missing i18n toggle and inconsistent theme chrome", () => {
  beforeEach(() => {
    localStorage.clear();
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

  it("exposes language toggle in admin layout chrome (regression for missing F31 toggle)", async () => {
    await renderAdmin("/corpus");
    expect(screen.getByTestId("language-toggle")).toBeInTheDocument();
  });

  it("exposes theme toggle on corpus route without opening mobile nav sheet", async () => {
    await renderAdmin("/corpus");
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });
});
