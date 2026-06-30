import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { UsersPage } from "@/pages/UsersPage";

import { renderWithProviders } from "./renderWithProviders";
import { installAuthenticatedSupabaseMock } from "./supabaseMock";

function renderUsersPage() {
  return renderWithProviders(
    <MemoryRouter>
      <UsersPage />
    </MemoryRouter>,
  );
}

const MOCK_USERS = {
  users: [
    {
      id: "11111111-1111-1111-1111-111111111111",
      email: "admin@example.org",
      role: "admin",
      status: "active",
      created_at: "2026-06-01T00:00:00Z",
      last_sign_in_at: "2026-06-28T12:00:00Z",
    },
    {
      id: "22222222-2222-2222-2222-222222222222",
      email: "pending@example.org",
      role: "viewer",
      status: "invited",
      created_at: "2026-06-02T00:00:00Z",
      last_sign_in_at: null,
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("UsersPage (TC-088, UJ-030/031)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
    installAuthenticatedSupabaseMock();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("lists operators and shows invite + row actions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(MOCK_USERS)),
    );

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("user-row")).toHaveLength(2);
    });
    expect(screen.getByText("admin@example.org")).toBeInTheDocument();
    expect(screen.getByTestId("users-invite-open")).toBeInTheDocument();
    expect(
      screen.getByTestId(
        `resend-invite-${MOCK_USERS.users[1]?.id ?? ""}`,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId(`delete-user-${MOCK_USERS.users[0]?.id ?? ""}`),
    ).toBeInTheDocument();
  });

  it("opens invite dialog and submits invite", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            id: "33333333-3333-3333-3333-333333333333",
            email: "new@example.org",
            role: "viewer",
            status: "invited",
            created_at: null,
            last_sign_in_at: null,
          },
          201,
        ),
      )
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS));

    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-invite-open")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("users-invite-open"));
    fireEvent.change(screen.getByTestId("users-invite-email"), {
      target: { value: "new@example.org" },
    });
    fireEvent.click(screen.getByTestId("users-invite-submit"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8001/admin/users/invite",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});
