import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import { IdleTimeoutGuard } from "@/components/IdleTimeoutGuard";

const signOutMock = vi.fn().mockResolvedValue(undefined);
const staySignedInMock = vi.fn();
const signOutNowMock = vi.fn();

vi.mock("@/hooks/useIdleTimeout", () => ({
  useIdleTimeout: () => ({
    showWarning: true,
    secondsRemaining: 42,
    staySignedIn: staySignedInMock,
    signOutNow: signOutNowMock,
  }),
}));

vi.mock("@/auth/authContext", async () => {
  const actual =
    await vi.importActual<typeof import("@/auth/authContext")>(
      "@/auth/authContext",
    );
  return {
    ...actual,
    useAuth: () => ({
      session: { user: { id: "u1" } },
      signOut: signOutMock,
      loading: false,
      isAdmin: true,
    }),
  };
});

const navigateMock = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe("IdleTimeoutGuard", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders warning dialog and wires stay signed in / sign out actions", () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <AuthProvider>
            <IdleTimeoutGuard />
          </AuthProvider>
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(screen.getByTestId("idle-timeout-warning")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("idle-timeout-stay-signed-in"));
    expect(staySignedInMock).toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("idle-timeout-sign-out-now"));
    expect(signOutNowMock).toHaveBeenCalled();
  });

  it("ignores dialog open-change callbacks", () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <AuthProvider>
            <IdleTimeoutGuard />
          </AuthProvider>
        </MemoryRouter>
      </LocaleProvider>,
    );
    const dialog = screen.getByRole("dialog");
    fireEvent.keyDown(dialog, { key: "Escape", code: "Escape" });
    expect(screen.getByTestId("idle-timeout-warning")).toBeInTheDocument();
  });
});
