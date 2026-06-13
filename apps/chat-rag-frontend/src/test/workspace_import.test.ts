import { describe, expect, it } from "vitest";

import type { Locale } from "vecinita-frontend-i18n";
import { t } from "vecinita-frontend-i18n";

describe("workspace import: chat-rag-frontend → frontend-i18n", () => {
  it("resolves vecinita-frontend-i18n via npm workspace link", () => {
    const locale: Locale = "en";
    expect(typeof t).toBe("function");
    expect(locale).toBe("en");
  });
});
