/**
 * Shared Beta badge / banner / nav chip for flaky admin surfaces (F86).
 * [Corpus: feature-list.md §F86]
 * [Corpus: user-journeys.md §UJ-099]
 */
import { ExternalLink } from "lucide-react";

import { BETA_FEEDBACK_ISSUE_URL } from "@/config/beta";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export type BetaFeatureKey = "finetune" | "playground";

export interface BetaFeatureNoticeProps {
  feature: BetaFeatureKey;
  /** Compact chip for sidebar nav (no banner). */
  compact?: boolean;
  className?: string;
  /** Override compact chip test id (e.g. beta-nav-chip-finetune). */
  "data-testid"?: string;
}

export function BetaFeatureNotice({
  feature,
  compact = false,
  className,
  "data-testid": dataTestId,
}: BetaFeatureNoticeProps) {
  const tr = useAdminT();
  const descriptionKey =
    feature === "finetune"
      ? "admin.beta.description.finetune"
      : "admin.beta.description.playground";

  if (compact) {
    return (
      <Badge
        variant="outline"
        className={cn(
          "shrink-0 border-amber-600/50 px-1.5 py-0 text-[10px] font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300",
          className,
        )}
        data-testid={dataTestId ?? "beta-feature-nav-chip"}
        title={tr("admin.beta.badgeTitle")}
      >
        {tr("admin.beta.badge")}
      </Badge>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-md border border-amber-600/40 bg-amber-50/80 px-3 py-2 text-sm text-amber-950 dark:border-amber-500/40 dark:bg-amber-950/40 dark:text-amber-50",
        className,
      )}
      data-testid={`beta-feature-banner-${feature}`}
      role="status"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant="outline"
          className="border-amber-700/50 bg-amber-100/80 text-amber-900 dark:border-amber-400/50 dark:bg-amber-900/50 dark:text-amber-100"
          data-testid="beta-feature-badge"
        >
          {tr("admin.beta.badge")}
        </Badge>
        <span className="font-medium">{tr("admin.beta.heading")}</span>
      </div>
      <p className="text-muted-foreground dark:text-amber-100/80">
        {tr(descriptionKey)}
      </p>
      <a
        href={BETA_FEEDBACK_ISSUE_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex w-fit items-center gap-1 font-medium text-amber-900 underline-offset-2 hover:underline dark:text-amber-100"
        data-testid={`beta-feature-feedback-link-${feature}`}
      >
        {tr("admin.beta.feedbackLink")}
        <ExternalLink className="h-3.5 w-3.5" aria-hidden />
      </a>
    </div>
  );
}
