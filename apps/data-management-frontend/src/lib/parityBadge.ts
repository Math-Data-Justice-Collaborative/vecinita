import type { DocumentSummary } from "@/api/types";

export type ParityGapKind = "missing_es" | "missing_en";

/** F76 / ADR-052 — parity from paired_document_id only. */
export function parityGapKind(
  document: Pick<DocumentSummary, "language" | "paired_document_id">,
): ParityGapKind | null {
  if (document.paired_document_id) {
    return null;
  }
  if (document.language === "en") {
    return "missing_es";
  }
  if (document.language === "es") {
    return "missing_en";
  }
  return null;
}
