import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "@/components/ThemeProvider";

import { AuditPage } from "@/pages/AuditPage";
import { UsersPage } from "@/pages/UsersPage";

import { renderWithProviders } from "./renderWithProviders";
import { installAuthenticatedSupabaseMock } from "./supabaseMock";

const USER_ID = "11111111-1111-1111-1111-111111111111";

const MIXED_AUDIT = {
  items: [
    {
      id: "evt-user-1",
      event_type: "user.invited",
      entity_type: "user",
      entity_id: USER_ID,
      request_id: "req-1",
      created_at: "2026-06-28T10:00:00Z",
      payload: { role: "viewer" },
    },
    {
      id: "evt-email-1",
      event_type: "email.test_sent",
      entity_type: "email",
      entity_id: "domain-uuid",
      request_id: "req-2",
      created_at: "2026-06-28T09:00:00Z",
      payload: { domain: "example.org", success: true },
    },
    {
      id: "evt-doc-1",
      event_type: "document.created",
      entity_type: "document",
      entity_id: "doc-aaa",
      request_id: "req-3",
      created_at: "2026-06-28T08:00:00Z",
      payload: {},
    },
  ],
  total_count: 3,
  page: 1,
  page_size: 50,
};

const MOCK_USERS = {
  users: [
    {
      id: USER_ID,
      email: "admin@example.org",
      role: "admin",
      status: "active",
      created_at: "2026-06-01T00:00:00Z",
      last_sign_in_at: "2026-06-28T12:00:00Z",
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
};

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderAudit(initialEntry = "/audit") {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AuditPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AuditPage user events (TC-101, UJ-038)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders friendly labels for user and email events", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => MIXED_AUDIT }),
    );

    renderAudit();

    await waitFor(() => {
      expect(screen.getByText("User invited")).toBeInTheDocument();
    });
    expect(screen.getByText("Test email sent")).toBeInTheDocument();
    expect(screen.getByText("document.created")).toBeInTheDocument();
  });

  it("filters by entity_type Users when applied", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => MIXED_AUDIT })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...MIXED_AUDIT,
          items: [MIXED_AUDIT.items[0]],
          total_count: 1,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderAudit();

    await waitFor(() => {
      expect(screen.getByTestId("filter-entity-type")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("filter-entity-type"));
    fireEvent.click(screen.getByRole("option", { name: /users/i }));
    fireEvent.click(screen.getByTestId("apply-filters"));

    await waitFor(() => {
      const lastUrl = fetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastUrl).toContain("entity_type=user");
    });
  });

  it("pre-filters by entity_id from the Users page view-activity link", async () => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
    installAuthenticatedSupabaseMock();

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...MIXED_AUDIT,
          items: [MIXED_AUDIT.items[0]],
          total_count: 1,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/users"]}>
          <Routes>
            <Route path="/users" element={<UsersPage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId(`view-activity-${USER_ID}`)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`view-activity-${USER_ID}`));

    await waitFor(() => {
      const auditCall = fetchMock.mock.calls.find((call) =>
        String(call[0]).includes("/internal/v1/audit"),
      );
      expect(auditCall?.[0]).toContain(`entity_id=${USER_ID}`);
    });
  });
});
