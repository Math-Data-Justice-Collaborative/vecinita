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

const PAGE_ONE = {
  users: [
    {
      id: "11111111-1111-1111-1111-111111111111",
      email: "alice@example.org",
      role: "admin",
      status: "active",
      created_at: "2026-06-01T00:00:00Z",
      last_sign_in_at: "2026-06-28T12:00:00Z",
    },
  ],
  total: 75,
  page: 1,
  page_size: 50,
};

const PAGE_TWO = {
  ...PAGE_ONE,
  users: [
    {
      id: "22222222-2222-2222-2222-222222222222",
      email: "bob@example.org",
      role: "viewer",
      status: "active",
      created_at: "2026-06-02T00:00:00Z",
      last_sign_in_at: null,
    },
  ],
  page: 2,
};

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("UsersPage search + pagination (TC-100, UJ-030)", () => {
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

  it("renders search controls and pagination, forwarding q and page params", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(PAGE_ONE))
      .mockResolvedValueOnce(jsonResponse(PAGE_ONE))
      .mockResolvedValueOnce(jsonResponse(PAGE_TWO));
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-search-input")).toBeInTheDocument();
    });
    expect(screen.getByTestId("pagination-controls")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("users-search-input"), {
      target: { value: "alice" },
    });
    fireEvent.click(screen.getByTestId("users-search-apply"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("q=alice"),
        expect.anything(),
      );
    });

    fireEvent.click(screen.getByTestId("pagination-next"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("page=2"),
        expect.anything(),
      );
    });
  });

  it("shows a validation message when the search query is too short", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(PAGE_ONE)));

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-search-input")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("users-search-input"), {
      target: { value: "ab" },
    });
    fireEvent.click(screen.getByTestId("users-search-apply"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/3 character/i);
  });

  it("applies search on Enter and clears q when search is emptied", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(PAGE_ONE));
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-search-input")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("users-search-input"), {
      target: { value: "alice" },
    });
    fireEvent.keyDown(screen.getByTestId("users-search-input"), {
      key: "Enter",
      code: "Enter",
    });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("q=alice"),
        expect.anything(),
      );
    });

    fireEvent.change(screen.getByTestId("users-search-input"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByTestId("users-search-apply"));

    await waitFor(() => {
      const lastUrl = fetchMock.mock.calls.at(-1)?.[0] as string;
      expect(lastUrl).not.toContain("q=");
    });
  });

  it("pagination previous requests page 1 after advancing", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(PAGE_ONE))
      .mockResolvedValueOnce(jsonResponse(PAGE_TWO))
      .mockResolvedValueOnce(jsonResponse(PAGE_ONE));
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("pagination-next")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("pagination-next"));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("page=2"),
        expect.anything(),
      );
    });

    fireEvent.click(screen.getByTestId("pagination-previous"));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("page=1"),
        expect.anything(),
      );
    });
  });
});
