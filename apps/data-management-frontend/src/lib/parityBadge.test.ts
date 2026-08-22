import { describe, expect, it } from "vitest";

import { parityGapKind } from "@/lib/parityBadge";

describe("parityGapKind", () => {
  it("returns missing_es for unpaired English documents", () => {
    expect(parityGapKind({ language: "en", paired_document_id: null })).toBe(
      "missing_es",
    );
  });

  it("returns missing_en for unpaired Spanish documents", () => {
    expect(parityGapKind({ language: "es", paired_document_id: null })).toBe(
      "missing_en",
    );
  });

  it("returns null when paired_document_id is set", () => {
    expect(
      parityGapKind({
        language: "en",
        paired_document_id: "635aa22e-c1a9-4c2f-b817-1adba92b2daf",
      }),
    ).toBeNull();
  });

  it("returns null for unsupported language codes", () => {
    expect(
      parityGapKind({ language: "fr", paired_document_id: null }),
    ).toBeNull();
  });
});
