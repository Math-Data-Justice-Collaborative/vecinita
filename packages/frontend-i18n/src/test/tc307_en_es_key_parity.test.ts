import { describe, expect, it } from "vitest";

import { stringMessages } from "../messages";
import { t } from "../t";

/**
 * TC-307 / EV-296 / #296 — full EN/ES key-set equality for frontend-i18n.
 * Also asserts ChatRAG visitor keys land under `chat.*` (welcomeHeading).
 */
describe("TC-307: frontend-i18n EN/ES key-set equality (F31, EV-296)", () => {
  it("has identical string key sets for en and es", () => {
    const enKeys = Object.keys(stringMessages.en).sort();
    const esKeys = Object.keys(stringMessages.es).sort();
    expect(esKeys).toEqual(enKeys);
  });

  it("includes ChatRAG visitor shell keys under chat.* namespace", () => {
    expect(t("en", "chat.welcomeHeading")).toBe("What can I help with?");
    expect(t("es", "chat.welcomeHeading")).toMatch(/ayudarte/i);
    expect(t("en", "chat.ask")).toBe("Ask");
    expect(t("es", "chat.ask")).toBe("Preguntar");
  });
});
