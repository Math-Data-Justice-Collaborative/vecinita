import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ACTION_ICON_MOTION_CLASS, ActionIcon } from "../ActionIcon";

describe("ActionIcon (TC-221, TC-222 / F66)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("applies spin class and aria-busy when pending refresh (TC-221)", () => {
    render(
      <ActionIcon motion="spin" pending data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    const el = screen.getByTestId("action-icon");
    expect(el).toHaveAttribute("aria-busy", "true");
    expect(el.className).toContain(ACTION_ICON_MOTION_CLASS.spin);
  });

  it("applies pulse class when pending send (TC-221)", () => {
    render(
      <ActionIcon motion="pulse" pending data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    expect(screen.getByTestId("action-icon").className).toContain(
      ACTION_ICON_MOTION_CLASS.pulse,
    );
  });

  it("applies shake class when pending destructive (TC-221)", () => {
    render(
      <ActionIcon motion="shake" pending data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    expect(screen.getByTestId("action-icon").className).toContain(
      ACTION_ICON_MOTION_CLASS.shake,
    );
  });

  it("does not apply motion class when not pending", () => {
    render(
      <ActionIcon motion="spin" pending={false} data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    const el = screen.getByTestId("action-icon");
    expect(el).not.toHaveAttribute("aria-busy");
    expect(el.className).not.toContain(ACTION_ICON_MOTION_CLASS.spin);
  });

  it("skips motion class when reducedMotion override is true (TC-222)", () => {
    render(
      <ActionIcon motion="spin" pending reducedMotion data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    const el = screen.getByTestId("action-icon");
    expect(el).toHaveAttribute("aria-busy", "true");
    expect(el.className).not.toContain(ACTION_ICON_MOTION_CLASS.spin);
  });

  it("skips motion when matchMedia prefers-reduced-motion (TC-222)", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("prefers-reduced-motion"),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
        onchange: null,
      })),
    );
    render(
      <ActionIcon motion="pulse" pending data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    expect(screen.getByTestId("action-icon").className).not.toContain(
      ACTION_ICON_MOTION_CLASS.pulse,
    );
  });

  it("merges className and defaults motion to spin", () => {
    render(
      <ActionIcon pending className="extra" data-testid="action-icon">
        icon
      </ActionIcon>,
    );
    const el = screen.getByTestId("action-icon");
    expect(el.className).toContain("extra");
    expect(el.className).toContain(ACTION_ICON_MOTION_CLASS.spin);
  });
});
