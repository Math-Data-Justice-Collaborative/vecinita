import { describe, expect, it } from "vitest";

import { formatRelativeTime } from "./relativeTime";

const NOW = 1_700_000_000_000;

describe("formatRelativeTime", () => {
  it("formats seconds in English", () => {
    expect(formatRelativeTime(NOW - 30_000, "en", NOW)).toMatch(
      /30 seconds ago/,
    );
  });

  it("formats minutes in English", () => {
    expect(formatRelativeTime(NOW - 5 * 60_000, "en", NOW)).toMatch(
      /5 minutes ago/,
    );
  });

  it("formats hours in English", () => {
    expect(formatRelativeTime(NOW - 3 * 3_600_000, "en", NOW)).toMatch(
      /3 hours ago/,
    );
  });

  it("formats days in English", () => {
    expect(formatRelativeTime(NOW - 2 * 86_400_000, "en", NOW)).toMatch(
      /2 days ago/,
    );
  });

  it("formats years (loop fall-through) in English", () => {
    expect(formatRelativeTime(NOW - 800 * 86_400_000, "en", NOW)).toMatch(
      /years ago/,
    );
  });

  it("formats in Spanish", () => {
    expect(formatRelativeTime(NOW - 2 * 3_600_000, "es", NOW)).toMatch(
      /hace 2 horas/,
    );
  });

  it("uses the current time when no reference is given", () => {
    expect(formatRelativeTime(Date.now(), "en")).toMatch(/now|second/i);
  });
});
