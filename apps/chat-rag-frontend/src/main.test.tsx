import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("main entry", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="root"></div>';
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ tags: [] }),
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.resetModules();
    vi.restoreAllMocks();
  });

  it("mounts the chat shell into #root", async () => {
    await import("./main");

    await waitFor(() => {
      expect(screen.getByTestId("app-header")).toBeInTheDocument();
    });
  });

  it("throws when #root is missing", async () => {
    document.body.innerHTML = "";
    await expect(import("./main")).rejects.toThrow(/root element/i);
  });
});
