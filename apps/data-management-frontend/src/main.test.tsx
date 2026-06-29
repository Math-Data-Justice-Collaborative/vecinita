import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { installAuthenticatedSupabaseMock } from "./test/supabaseMock";

const STATS = {
  total_documents: 0,
  total_chunks: 0,
  tag_distribution: [],
  language_breakdown: {},
  recent_activity: [],
  top_served: [],
};

describe("main entry", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="root"></div>';
    installAuthenticatedSupabaseMock();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(STATS),
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.resetModules();
    vi.restoreAllMocks();
  });

  it("mounts the admin shell into #root", async () => {
    await import("./main");

    await waitFor(
      () => {
        expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
      },
      { timeout: 10_000 },
    );
  }, 15_000);

  it("throws when #root is missing", async () => {
    vi.resetModules();
    document.body.innerHTML = "";
    await expect(import("./main")).rejects.toThrow(/root element/i);
  }, 15_000);
});
