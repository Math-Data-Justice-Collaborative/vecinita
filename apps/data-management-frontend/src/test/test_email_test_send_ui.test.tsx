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

describe("UsersPage send test email (TC-099, UJ-037)", () => {
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

  it("sends a test email via the admin endpoint and shows the message id", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(
        jsonResponse({ message_id: "re_test_abc123" }, 202),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-send-test-email")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("users-test-email-input"), {
      target: { value: "ops@partner.example.org" },
    });
    fireEvent.click(screen.getByTestId("users-send-test-email"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8001/admin/email/test",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ to: "ops@partner.example.org" }),
        }),
      );
    });

    const success = await screen.findByTestId("email-test-success");
    expect(success.textContent ?? "").toContain("re_test_abc123");
  });

  it("shows the deliverability checklist link when email is unconfigured (503)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: {
              code: "email_unconfigured",
              message: "Deliverability test-send is not configured",
            },
          },
          503,
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-send-test-email")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("users-test-email-input"), {
      target: { value: "ops@partner.example.org" },
    });
    fireEvent.click(screen.getByTestId("users-send-test-email"));

    const alert = await screen.findByTestId("email-test-unconfigured");
    expect(alert).toBeInTheDocument();
    expect(screen.getByTestId("email-test-checklist-link")).toHaveAttribute(
      "href",
      expect.stringContaining("staging-runbook"),
    );
  });

  it("shows the deliverability checklist link when the Resend domain is unverified (503)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(MOCK_USERS))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: {
              code: "domain_unverified",
              message:
                "The vecinita.admin domain is not verified. Please, add and verify your domain on https://resend.com/domains",
            },
          },
          503,
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderUsersPage();

    await waitFor(() => {
      expect(screen.getByTestId("users-send-test-email")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("users-test-email-input"), {
      target: { value: "ops@partner.example.org" },
    });
    fireEvent.click(screen.getByTestId("users-send-test-email"));

    const alert = await screen.findByTestId("email-test-domain-unverified");
    expect(alert).toBeInTheDocument();
    expect(screen.getByTestId("email-test-checklist-link")).toHaveAttribute(
      "href",
      expect.stringContaining("staging-runbook"),
    );
  });
});
