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

async function openSignOutMore(): Promise<void> {
  const more = screen.getByTestId("admin-sign-out-more");
  const summary = more.querySelector("summary");
  expect(summary).not.toBeNull();
  fireEvent.click(summary!);
  await waitFor(() => {
    expect(
      screen.getByTestId("admin-sign-out-all-devices"),
    ).toBeInTheDocument();
  });
}

describe("log out of all devices (UJ-035, TC-097 / TC-331)", () => {
  beforeEach(() => {
    mockSignOut.mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("keeps Sign out primary and demotes log out of all devices (UX-5)", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    expect(screen.getByTestId("admin-sign-out")).toHaveAttribute(
      "data-priority",
      "primary",
    );
    expect(screen.getByTestId("admin-sign-out-more")).toBeInTheDocument();
    await openSignOutMore();
    expect(screen.getByTestId("admin-sign-out-all-devices")).toHaveAttribute(
      "data-priority",
      "secondary",
    );
  });

  it("uses global signOut for all devices and local scope for standard logout", async () => {
    renderSignedInApp("/dashboard");
    await waitForAdminNav();

    await openSignOutMore();
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
