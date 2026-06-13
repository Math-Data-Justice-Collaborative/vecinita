/**
 * BUG-2026-05-27: Audit page blank when /internal/v1/audit returns api-contract shape.
 * @see docs/bug-reports/BUG-2026-05-27-audit-page-blank.md
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import { AuditPage } from "@/pages/AuditPage";

/** Production / api-contract response (items, total_count, created_at). */
const PRODUCTION_AUDIT_RESPONSE = {
  items: [
    {
      id: "8c0d2bef-f472-4674-8090-6c8050622035",
      event_type: "document.deleted",
      entity_type: "document",
      entity_id: "4a435fec-f19f-40ea-a2dd-08417012ecb9",
      request_id: "44c448e7-7b1c-4cb9-9b6c-4a40b1d87254",
      payload: { url: "https://example.com/tag-caps/51c6f33c", title: null },
      created_at: "2026-05-27T21:41:55.326715Z",
    },
    {
      id: "65570ecf-349f-4efc-beeb-36c920011cbb",
      event_type: "document.tagged",
      entity_type: "document",
      entity_id: "18799e37-372a-4ad4-a859-cecb65eb90fd",
      request_id: "69105205-a814-464e-a803-0c6a1fbfbcda",
      payload: {
        tags: [{ slug: "housing", label: "Housing", source: "human" }],
      },
      created_at: "2026-05-27T14:48:53.457930Z",
    },
  ],
  page: 1,
  page_size: 50,
  total_count: 14,
};

function renderAudit() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <AuditPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("BUG-2026-05-27 audit page blank on api-contract shape", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders audit table when API returns items + total_count + created_at", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => PRODUCTION_AUDIT_RESPONSE,
      }),
    );

    renderAudit();

    await waitFor(() => {
      expect(screen.getByText("document.deleted")).toBeInTheDocument();
    });
    expect(screen.getByText("document.tagged")).toBeInTheDocument();
    expect(screen.getByText(/showing 2 of 14 events/i)).toBeInTheDocument();
  });
});
