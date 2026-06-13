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
