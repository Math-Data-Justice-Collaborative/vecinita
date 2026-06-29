import { describe, expect, it } from "vitest";

import { t } from "../t";

describe("t() parameter interpolation", () => {
  it("substitutes a single named parameter into the template", () => {
    expect(t("en", "admin.auth.currentUser", { email: "admin@vecinita" })).toBe(
      "Signed in as admin@vecinita",
    );
  });

  it("substitutes numeric parameters, coercing them to strings", () => {
    expect(t("en", "admin.corpusList.selectedCount", { count: 3 })).toBe(
      "3 selected",
    );
  });

  it("replaces every occurrence of a repeated placeholder", () => {
    expect(t("es", "admin.audit.showingCount", { shown: 5, total: 20 })).toBe(
      "Mostrando 5 de 20 eventos",
    );
  });

  it("returns the raw template when no params are supplied", () => {
    expect(t("en", "admin.auth.currentUser")).toBe("Signed in as {email}");
  });
});
