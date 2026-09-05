import { describe, expect, it } from "vitest";

import { t } from "vecinita-frontend-i18n";

describe("messages (package chat.* / shared.*)", () => {
  it("returns English strings for simple keys", () => {
    expect(t("en", "chat.ask")).toBe("Ask");
    expect(t("en", "chat.navCorpus")).toBe("Corpus");
  });

  it("returns Spanish strings for simple keys", () => {
    expect(t("es", "chat.ask")).toBe("Preguntar");
    expect(t("es", "chat.loadTagsFailed")).toMatch(/etiquetas/i);
  });

  it("provides the redesign welcome + sidebar strings in both locales", () => {
    expect(t("en", "chat.welcomeHeading")).toBe("What can I help with?");
    expect(t("es", "chat.welcomeHeading")).toMatch(/ayudarte/i);
    expect(t("en", "chat.suggestion1")).toBe(
      "Where can I get food assistance in Rhode Island?",
    );
    expect(t("es", "chat.suggestion1")).toBe(
      "¿Dónde puedo conseguir ayuda con comida en Rhode Island?",
    );
    expect(t("en", "chat.suggestion2")).toBe(
      "How do I get rent assistance in Providence?",
    );
    expect(t("es", "chat.suggestion2")).toBe(
      "¿Cómo solicito ayuda para pagar el alquiler en Providence?",
    );
    expect(t("en", "chat.suggestion3")).toBe(
      "Where can I find free ESL classes in Providence?",
    );
    expect(t("es", "chat.suggestion3")).toBe(
      "¿Dónde puedo encontrar clases gratis de inglés en Providence?",
    );
    expect(t("en", "chat.questionPlaceholder")).toBe(
      "e.g. Where can I get food assistance?",
    );
    expect(t("es", "chat.questionPlaceholder")).toBe(
      "p. ej. ¿Dónde puedo conseguir ayuda con comida?",
    );
    expect(t("en", "chat.toggleSidebar")).toMatch(/menu/i);
    expect(t("es", "chat.toggleSidebar")).toMatch(/menú/i);
    expect(t("en", "chat.switchToDark")).toMatch(/dark/i);
    expect(t("es", "chat.switchToLight")).toMatch(/claro/i);
  });

  it("formats pagination for both locales via shared.pagination", () => {
    expect(t("en", "shared.pagination", 2, 5, 42)).toBe(
      "Page 2 of 5 (42 documents)",
    );
    expect(t("es", "shared.pagination", 1, 3, 10)).toBe(
      "Página 1 de 3 (10 documentos)",
    );
  });

  it("formats pagination with default page arguments", () => {
    expect(
      t(
        "en",
        "shared.pagination",
        undefined as unknown as number,
        undefined as unknown as number,
        undefined as unknown as number,
      ),
    ).toBe("Page 1 of 1 (0 documents)");
  });
});
