import { describe, expect, it } from "vitest";

import { t } from "./messages";

describe("messages", () => {
  it("returns English strings for simple keys", () => {
    expect(t("en", "ask")).toBe("Ask");
    expect(t("en", "navCorpus")).toBe("Corpus");
  });

  it("returns Spanish strings for simple keys", () => {
    expect(t("es", "ask")).toBe("Preguntar");
    expect(t("es", "loadTagsFailed")).toMatch(/etiquetas/i);
  });

  it("provides the redesign welcome + sidebar strings in both locales", () => {
    expect(t("en", "welcomeHeading")).toBe("What can I help with?");
    expect(t("es", "welcomeHeading")).toMatch(/ayudarte/i);
    // TC-259 / EV-216 — corpus-aligned suggested chips
    expect(t("en", "suggestion1")).toBe(
      "Where can I get food assistance in Rhode Island?",
    );
    expect(t("es", "suggestion1")).toBe(
      "¿Dónde puedo conseguir ayuda con comida en Rhode Island?",
    );
    expect(t("en", "suggestion2")).toBe(
      "How do I get rent assistance in Providence?",
    );
    expect(t("es", "suggestion2")).toBe(
      "¿Cómo solicito ayuda para pagar el alquiler en Providence?",
    );
    expect(t("en", "suggestion3")).toBe(
      "Where can I find free ESL classes in Providence?",
    );
    expect(t("es", "suggestion3")).toBe(
      "¿Dónde puedo encontrar clases gratis de inglés en Providence?",
    );
    expect(t("en", "questionPlaceholder")).toBe(
      "e.g. Where can I get food assistance?",
    );
    expect(t("es", "questionPlaceholder")).toBe(
      "p. ej. ¿Dónde puedo conseguir ayuda con comida?",
    );
    expect(t("en", "toggleSidebar")).toMatch(/menu/i);
    expect(t("es", "toggleSidebar")).toMatch(/menú/i);
    expect(t("en", "switchToDark")).toMatch(/dark/i);
    expect(t("es", "switchToLight")).toMatch(/claro/i);
  });

  it("formats pagination for both locales", () => {
    expect(t("en", "pagination", 2, 5, 42)).toBe("Page 2 of 5 (42 documents)");
    expect(t("es", "pagination", 1, 3, 10)).toBe(
      "Página 1 de 3 (10 documentos)",
    );
  });

  it("formats pagination with default page arguments", () => {
    expect(
      t(
        "en",
        "pagination",
        undefined as unknown as number,
        undefined as unknown as number,
        undefined as unknown as number,
      ),
    ).toBe("Page 1 of 1 (0 documents)");
  });
});
