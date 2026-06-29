import { cleanup, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "./renderWithProviders";
import { DashboardPage } from "@/pages/DashboardPage";
import { HealthPage } from "@/pages/HealthPage";
import { AuditPage } from "@/pages/AuditPage";

/**
 * BUG-2026-06-29 (QA-S004-010): admin pages that fetch on mount called
 * `setState` after unmount when the pending request settled post-teardown,
 * surfacing as an `Unhandled Rejection: window is not defined` that crashed the
 * Vitest worker (npm exit 1) even though every assertion passed. The fix mirrors
 * the BUG-2026-06-14 CorpusList guard: an `isActive()` check before each state
 * update, flipped off by the effect cleanup on unmount.
 */
const PAGES = [
  { name: "DashboardPage", Component: DashboardPage },
  { name: "HealthPage", Component: HealthPage },
  { name: "AuditPage", Component: AuditPage },
] as const;

describe("BUG-2026-06-29 admin page unmount during load", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  for (const { name, Component } of PAGES) {
    it(`does not set state after ${name} unmounts while fetch is pending`, async () => {
      const unhandled: unknown[] = [];
      const onRejection = (reason: unknown) => {
        unhandled.push(reason);
      };
      process.on("unhandledRejection", onRejection);

      let resolveFetch: (value: Response) => void = () => undefined;
      const pendingFetch = new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });
      vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

      try {
        const { unmount } = renderWithProviders(
          <MemoryRouter>
            <Component />
          </MemoryRouter>,
        );
        expect(screen.getByText(/loading/i)).toBeInTheDocument();

        unmount();

        resolveFetch({
          ok: true,
          // Superset payload that satisfies the stats, health, and audit parsers
          // so each page reaches its post-await `isActive()` guard (the inactive
          // branch under test) rather than diverging into the catch path.
          json: async () => ({
            total_documents: 0,
            total_chunks: 0,
            tag_distribution: [],
            language_breakdown: {},
            recent_activity: [],
            top_served: [],
            status: "healthy",
            services: {},
            checked_at: "2026-06-29T00:00:00Z",
            items: [],
            page: 1,
            page_size: 50,
            total_count: 0,
          }),
        } as Response);

        await new Promise((resolve) => {
          setTimeout(resolve, 50);
        });

        expect(unhandled).toEqual([]);
      } finally {
        process.off("unhandledRejection", onRejection);
      }
    });

    it(`does not set state after ${name} unmounts while fetch rejects`, async () => {
      const unhandled: unknown[] = [];
      const onRejection = (reason: unknown) => {
        unhandled.push(reason);
      };
      process.on("unhandledRejection", onRejection);

      let rejectFetch: (reason: Error) => void = () => undefined;
      const pendingFetch = new Promise<Response>((_resolve, reject) => {
        rejectFetch = reject;
      });
      vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

      try {
        const { unmount } = renderWithProviders(
          <MemoryRouter>
            <Component />
          </MemoryRouter>,
        );
        expect(screen.getByText(/loading/i)).toBeInTheDocument();

        unmount();
        rejectFetch(new Error("network down"));

        await new Promise((resolve) => {
          setTimeout(resolve, 50);
        });

        expect(unhandled).toEqual([]);
      } finally {
        process.off("unhandledRejection", onRejection);
      }
    });
  }
});
