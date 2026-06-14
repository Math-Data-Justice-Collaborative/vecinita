import { describe, expect, it } from "vitest";

import { t } from "../t";

describe("TC-067: frontend-i18n message keys and t()", () => {
  it("resolves shared.pagination for EN with page, totalPages, total", () => {
    expect(t("en", "shared.pagination", 1, 3, 42)).toBe(
      "Page 1 of 3 (42 documents)",
    );
  });

  it("resolves shared.pagination for ES with page, totalPages, total", () => {
    expect(t("es", "shared.pagination", 1, 3, 42)).toBe(
      "Página 1 de 3 (42 documentos)",
    );
  });

  it("returns different EN and ES strings for shared.previous", () => {
    const enLabel = t("en", "shared.previous");
    const esLabel = t("es", "shared.previous");
    expect(enLabel).toBe("Previous");
    expect(esLabel).toBe("Anterior");
    expect(enLabel).not.toBe(esLabel);
  });

  it("resolves simple dot-prefixed string keys per locale", () => {
    expect(t("en", "shared.next")).toBe("Next");
    expect(t("es", "shared.next")).toBe("Siguiente");
  });

  it("returns distinct EN/ES strings for chat namespace samples", () => {
    expect(t("en", "chat.ask")).toBe("Ask");
    expect(t("es", "chat.ask")).toBe("Preguntar");
  });
});
