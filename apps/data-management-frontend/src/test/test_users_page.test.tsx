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
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MOCK_USERS)));

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("user-row")).toHaveLength(2);
    });
    expect(screen.getByText("admin@example.org")).toBeInTheDocument();
    expect(screen.getByTestId("users-invite-open")).toBeInTheDocument();
    expect(
      screen.getByTestId(`resend-invite-${MOCK_USERS.users[1]?.id ?? ""}`),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId(`delete-user-${MOCK_USERS.users[0]?.id ?? ""}`),
    ).toBeInTheDocument();
  });

  const MIXED_USERS = {
    users: [
      {
        id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        email: "admin@example.org",
        role: "admin",
        status: "active",
        created_at: "2026-06-01T00:00:00Z",
        last_sign_in_at: "2026-06-28T12:00:00Z",
      },
      {
        id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        email: "viewer@example.org",
        role: "viewer",
        status: "active",
        created_at: "2026-06-02T00:00:00Z",
        last_sign_in_at: null,
      },
      {
        id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
        email: "disabled@example.org",
        role: "viewer",
        status: "disabled",
        created_at: "2026-06-03T00:00:00Z",
        last_sign_in_at: null,
      },
      {
        id: "dddddddd-dddd-dddd-dddd-dddddddddddd",
        email: "invited@example.org",
        role: "viewer",
        status: "invited",
        created_at: "2026-06-04T00:00:00Z",
        last_sign_in_at: null,
      },
    ],
    total: 4,
    page: 1,
    page_size: 50,
  };

  const ADMIN_ID = MIXED_USERS.users[0]?.id ?? "";
  const VIEWER_ID = MIXED_USERS.users[1]?.id ?? "";
  const DISABLED_ID = MIXED_USERS.users[2]?.id ?? "";
  const INVITED_ID = MIXED_USERS.users[3]?.id ?? "";

  it("renders status-specific row actions for each operator", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(MIXED_USERS)),
    );
    renderUsersPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("user-row")).toHaveLength(4);
    });

    expect(screen.getByTestId(`demote-user-${ADMIN_ID}`)).toBeInTheDocument();
    expect(screen.getByTestId(`force-signout-${ADMIN_ID}`)).toBeInTheDocument();
    expect(screen.getByTestId(`promote-user-${VIEWER_ID}`)).toBeInTheDocument();
    expect(
      screen.getByTestId(`enable-user-${DISABLED_ID}`),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId(`resend-invite-${INVITED_ID}`),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId(`force-signout-${DISABLED_ID}`),
    ).not.toBeInTheDocument();
  });

  it("runs each row action against its endpoint", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation((url: string, init?: RequestInit) => {
        if (!init || init.method === undefined || init.method === "GET") {
          return Promise.resolve(jsonResponse(MIXED_USERS));
        }
        return Promise.resolve(jsonResponse({ acknowledged: true }, 202));
      });
    vi.stubGlobal("fetch", fetchMock);
    renderUsersPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("user-row")).toHaveLength(4);
    });

    const cases: [string, string, string][] = [
      [`demote-user-${ADMIN_ID}`, `/admin/users/${ADMIN_ID}/role`, "PATCH"],
      [`disable-user-${ADMIN_ID}`, `/admin/users/${ADMIN_ID}/disable`, "POST"],
      [
        `reset-password-${VIEWER_ID}`,
        `/admin/users/${VIEWER_ID}/reset-password`,
        "POST",
      ],
      [`promote-user-${VIEWER_ID}`, `/admin/users/${VIEWER_ID}/role`, "PATCH"],
      [
        `enable-user-${DISABLED_ID}`,
        `/admin/users/${DISABLED_ID}/enable`,
        "POST",
      ],
      [
        `resend-invite-${INVITED_ID}`,
        `/admin/users/${INVITED_ID}/resend-invite`,
        "POST",
      ],
      [`delete-user-${INVITED_ID}`, `/admin/users/${INVITED_ID}`, "DELETE"],
    ];

    for (const [testId, path, method] of cases) {
      fetchMock.mockClear();
      fireEvent.click(screen.getByTestId(testId));
      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          `http://localhost:8001${path}`,
          expect.objectContaining({ method }),
        );
      });
    }
  });

  it("surfaces an error when a row action fails", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation((_url: string, init?: RequestInit) => {
        if (!init || init.method === undefined || init.method === "GET") {
          return Promise.resolve(jsonResponse(MIXED_USERS));
        }
        return Promise.resolve(new Response("disable boom", { status: 500 }));
      });
    vi.stubGlobal("fetch", fetchMock);
    renderUsersPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(`disable-user-${ADMIN_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`disable-user-${ADMIN_ID}`));

    expect(await screen.findByRole("alert")).toHaveTextContent("disable boom");
  });

  it("falls back to the generic message when an action rejects with a non-Error", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation((_url: string, init?: RequestInit) => {
        if (!init || init.method === undefined || init.method === "GET") {
          return Promise.resolve(jsonResponse(MIXED_USERS));
        }
        // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- exercises the non-Error catch fallback branch
        return Promise.reject("string failure");
      });
    vi.stubGlobal("fetch", fetchMock);
    renderUsersPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(`disable-user-${ADMIN_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`disable-user-${ADMIN_ID}`));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /failed to load users/i,
    );
  });

  it("surfaces an error when the invite request fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MIXED_USERS))
      .mockResolvedValueOnce(new Response("invite boom", { status: 422 }));
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

    expect(await screen.findByText("invite boom")).toBeInTheDocument();
  });

  it("shows empty state when no operators match", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ users: [], total: 0, page: 1, page_size: 50 }),
        ),
    );

    renderUsersPage();

    expect(await screen.findByText(/no operators/i)).toBeInTheDocument();
  });

  it("surfaces load errors from the list endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("list failed", { status: 500 })),
    );

    renderUsersPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("list failed");
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

  it("shows retract invitation only for invited rows (TC-108)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MOCK_USERS)));

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getAllByTestId("user-row")).toHaveLength(2);
    });

    const invitedId = MOCK_USERS.users[1]?.id ?? "";
    expect(
      screen.getByTestId(`revoke-invite-${invitedId}`),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId(`revoke-invite-${MOCK_USERS.users[0]?.id ?? ""}`),
    ).not.toBeInTheDocument();
  });

  it("calls revoke-invite endpoint when retract is clicked (TC-108)", async () => {
    const invitedId = MOCK_USERS.users[1]?.id ?? "";
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(jsonResponse({}, 202))
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS));

    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId(`revoke-invite-${invitedId}`)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`revoke-invite-${invitedId}`));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost:8001/admin/users/${invitedId}/revoke-invite`,
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});
