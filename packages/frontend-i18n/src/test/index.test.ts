import { describe, expect, it } from "vitest";

import * as i18n from "../index";

describe("frontend-i18n public exports", () => {
  it("re-exports the locale helpers and t()", () => {
    expect(i18n.LOCALE_STORAGE_KEY).toBe("vecinita.locale");
    expect(typeof i18n.detectBrowserLocale).toBe("function");
    expect(typeof i18n.readStoredLocale).toBe("function");
    expect(typeof i18n.t).toBe("function");
    expect(i18n.t("en", "shared.next")).toBe("Next");
  });
});
