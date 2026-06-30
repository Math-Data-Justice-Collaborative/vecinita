vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

import { cleanup, fireEvent, screen, waitFor, act } from "@testing-library/react";
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

describe("auth UX privacy — no extra server traffic (TC-102)", () => {
  const fetchMock = vi.fn();

  function adminApiCallCount(): number {
    return fetchMock.mock.calls.filter(([url]) =>
      String(url).includes("/admin/"),
    ).length;
  }

  beforeEach(() => {
    mockSignOut.mockClear();
    fetchMock.mockReset();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        total_count: 0,
        page: 1,
        page_size: 50,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("idle timeout only calls Supabase signOut, not Vecinita admin APIs", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    const callsBeforeIdle = adminApiCallCount();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10_000);
    });

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith({ scope: "local" });
    });

    expect(adminApiCallCount()).toBe(callsBeforeIdle);
  });

  it("log out of all devices only calls Supabase signOut", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    const callsBefore = adminApiCallCount();

    fireEvent.click(screen.getByTestId("admin-sign-out-all-devices"));

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith();
    });

    expect(adminApiCallCount()).toBe(callsBefore);
  });
});
