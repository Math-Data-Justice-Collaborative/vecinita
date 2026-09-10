/** Regression: chat shell defaults sidebar closed on narrow viewports. */

import { describe, expect, it } from "vitest";

import { initialSidebarOpen } from "../lib/sidebarInitial";

describe("initialSidebarOpen (responsive UX)", () => {
  it("opens by default on desktop widths", () => {
    expect(initialSidebarOpen(1280)).toBe(true);
    expect(initialSidebarOpen(769)).toBe(true);
  });

  it("stays closed on phone/tablet drawer widths", () => {
    expect(initialSidebarOpen(375)).toBe(false);
    expect(initialSidebarOpen(768)).toBe(false);
  });
});
