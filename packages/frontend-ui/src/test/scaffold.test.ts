import { describe, expect, it } from "vitest";

describe("frontend-ui package exports", () => {
  it("exposes the public component and locale API surface", async () => {
    const ui = await import("../index");
    expect(typeof ui.LanguageToggle).toBe("function");
    expect(typeof ui.LocaleProvider).toBe("function");
    expect(typeof ui.useLocale).toBe("function");
  });
});
