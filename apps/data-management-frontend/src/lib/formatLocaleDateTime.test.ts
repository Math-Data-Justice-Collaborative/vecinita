import { describe, expect, it } from "vitest";

import { formatLocaleDateTime } from "./formatLocaleDateTime";

describe("formatLocaleDateTime", () => {
  it("formats timestamps for English and Spanish locales", () => {
    const value = "2026-06-15T12:00:00.000Z";

    expect(formatLocaleDateTime("en", value)).toContain("2026");
    expect(formatLocaleDateTime("es", value)).toContain("2026");
  });
});
