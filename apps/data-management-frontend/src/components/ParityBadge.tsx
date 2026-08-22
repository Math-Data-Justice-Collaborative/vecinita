import { Badge } from "@/components/ui/badge";
import type { DocumentSummary } from "@/api/types";
import { parityGapKind } from "@/lib/parityBadge";
import { useAdminT } from "@/hooks/useAdminT";

type ParityBadgeProps = {
  document: Pick<DocumentSummary, "language" | "paired_document_id">;
};

export function ParityBadge({ document }: ParityBadgeProps) {
  const tr = useAdminT();
  const kind = parityGapKind(document);
  if (!kind) {
    return null;
  }
  const label =
    kind === "missing_es"
      ? tr("admin.corpus.parity.missingEs")
      : tr("admin.corpus.parity.missingEn");
  return (
    <Badge
      variant="outline"
      data-testid={`parity-badge-${kind}`}
      className="mt-1"
    >
      {label}
    </Badge>
  );
}
