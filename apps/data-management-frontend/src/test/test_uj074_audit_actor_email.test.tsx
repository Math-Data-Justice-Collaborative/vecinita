/**
 * UJ-074 / F69 — Audit Log shows actor email or truncated UUID.
 */
import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { AuditPage } from "@/pages/AuditPage";
import { renderWithProviders } from "./renderWithProviders";

const ACTOR_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";

function renderAudit() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <AuditPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("UJ-074 Audit actor email (F69)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders actor_email when present on audit items", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [
            {
              id: "evt-1",
              event_type: "document.edited",
              entity_type: "document",
              entity_id: "doc-1",
              request_id: "req-1",
              created_at: "2026-08-04T12:00:00Z",
              payload: {},
              actor_id: ACTOR_ID,
              actor_email: "operator@example.com",
            },
          ],
          total_count: 1,
          page: 1,
          page_size: 50,
        }),
      }),
    );

    renderAudit();

    await waitFor(() => {
      expect(screen.getByTestId("audit-actor-label")).toHaveTextContent(
        "operator@example.com",
      );
    });
  });

  it("renders truncated actor_id when actor_email is null", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [
            {
              id: "evt-2",
              event_type: "document.edited",
              entity_type: "document",
              entity_id: "doc-2",
              request_id: "req-2",
              created_at: "2026-08-04T12:00:00Z",
              payload: {},
              actor_id: ACTOR_ID,
              actor_email: null,
            },
          ],
          total_count: 1,
          page: 1,
          page_size: 50,
        }),
      }),
    );

    renderAudit();

    await waitFor(() => {
      expect(screen.getByTestId("audit-actor-label")).toHaveTextContent(
        "aaaaaaaa…",
      );
    });
  });
});
