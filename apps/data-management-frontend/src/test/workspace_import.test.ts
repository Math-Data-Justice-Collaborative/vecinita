import { describe, expect, it } from "vitest";

import type { Locale } from "vecinita-frontend-i18n";
import { t } from "vecinita-frontend-i18n";

describe("workspace import: data-management-frontend → frontend-i18n", () => {
  it("resolves vecinita-frontend-i18n via npm workspace link", () => {
    const locale: Locale = "es";
    expect(typeof t).toBe("function");
    expect(locale).toBe("es");
  });
});

describe("workspace import: data-management-frontend → frontend-ui", () => {
  it("resolves vecinita-frontend-ui via npm workspace link", async () => {
    const ui = await import("vecinita-frontend-ui");
    expect(ui).toBeDefined();
  });
});
