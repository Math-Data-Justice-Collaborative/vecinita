vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  mockSignOut,
  renderSignedInApp,
  waitForAdminNav,
} from "./authSessionHarness";

describe("log out of all devices (UJ-035, TC-097)", () => {
  beforeEach(() => {
    mockSignOut.mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("uses global signOut for all devices and local scope for standard logout", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    fireEvent.click(screen.getByTestId("admin-sign-out-all-devices"));
    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith();
    });

    mockSignOut.mockClear();
    fireEvent.click(screen.getByTestId("admin-sign-out"));
    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalledWith({ scope: "local" });
    });
  });
});
