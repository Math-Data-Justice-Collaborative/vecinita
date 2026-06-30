vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
  act,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  mockSignOut,
  renderSignedInApp,
  waitForAdminNav,
} from "./authSessionHarness";

vi.mock("@/config", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/config")>();
  return {
    ...actual,
    idleTimeoutMinutes: () => 1,
    idleWarningSeconds: () => 10,
  };
});

describe("idle timeout (UJ-034, TC-096)", () => {
  beforeEach(() => {
    mockSignOut.mockClear();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("shows warning at idle threshold then signs out locally", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    expect(screen.getByTestId("idle-timeout-warning")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });
    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith({ scope: "local" });
    });
  });

  it("signs out immediately when the operator chooses sign out now", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    fireEvent.click(screen.getByTestId("idle-timeout-sign-out-now"));

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith({ scope: "local" });
    });
  });

  it("resets the timer when the operator stays signed in", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    fireEvent.click(screen.getByTestId("idle-timeout-stay-signed-in"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    expect(screen.getByTestId("idle-timeout-warning")).toBeInTheDocument();
    expect(mockSignOut).not.toHaveBeenCalled();
  });
});
