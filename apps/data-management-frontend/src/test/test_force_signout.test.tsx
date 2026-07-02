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

const ACTIVE_USER_ID = "11111111-1111-1111-1111-111111111111";

const MOCK_USERS = {
  users: [
    {
      id: ACTIVE_USER_ID,
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

describe("UsersPage force sign-out (TC-098, UJ-036)", () => {
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

  it("force-signs out an active operator via the signout endpoint", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(jsonResponse({ acknowledged: true }, 202))
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS));
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `http://localhost:8001/admin/users/${ACTIVE_USER_ID}/signout`,
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("surfaces the disable fallback when the session-revoke RPC is unavailable (503)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: {
              code: "mechanism_unavailable",
              message:
                "Session-revoke RPC is not applied to the Supabase project",
            },
          },
          503,
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`));

    const fallback = await screen.findByTestId("force-signout-fallback");
    expect(fallback).toBeInTheDocument();
    expect(fallback.textContent ?? "").toMatch(/disable/i);
  });

  it("surfaces generic force-signout errors", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(new Response("signout failed", { status: 500 }));
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId(`force-signout-${ACTIVE_USER_ID}`));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /signout failed/i,
    );
    expect(
      screen.queryByTestId("force-signout-fallback"),
    ).not.toBeInTheDocument();
  });
});
