import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

import { usePlaygroundModelDownload } from "./usePlaygroundModelDownload";

export function ModelDownloadProgressIndicator({
  className,
  testId,
}: {
  className?: string;
  testId?: string;
}) {
  const tr = useAdminT();
  const { downloadStatus } = usePlaygroundModelDownload();

  if (downloadStatus !== "pulling") {
    return null;
  }

  return (
    <Badge
      variant="secondary"
      className={cn("gap-1 font-normal", className)}
      data-testid={testId}
    >
      <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
      {tr("admin.evaluation.models.downloadPulling")}
    </Badge>
  );
}
