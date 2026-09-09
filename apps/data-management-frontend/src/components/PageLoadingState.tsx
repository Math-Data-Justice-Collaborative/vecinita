import { t } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

import { Button } from "@/components/ui/button";

type PageLoadingStateProps = {
  timedOut?: boolean;
  onRetry?: () => void;
};

/**
 * Skeleton loading state for admin pages (UX-3). Prefer over plain "Loading…".
 */
export function PageLoadingState({
  timedOut = false,
  onRetry,
}: PageLoadingStateProps) {
  const { locale } = useLocale();

  return (
    <div
      role="status"
      aria-busy="true"
      aria-live="polite"
      data-testid="page-loading"
      className="space-y-4"
    >
      <p className="sr-only">{t(locale, "shared.loading")}</p>
      {timedOut ? (
        <div className="space-y-2" data-testid="page-loading-slow">
          <p className="text-sm text-muted-foreground">
            {t(locale, "shared.pageLoading.slow")}
          </p>
          {onRetry ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              data-testid="page-loading-retry"
              onClick={onRetry}
            >
              {t(locale, "shared.pageLoading.retry")}
            </Button>
          ) : null}
        </div>
      ) : null}
      <div
        className="animate-pulse space-y-4"
        data-testid="page-loading-skeletons"
        aria-hidden="true"
      >
        <div className="h-8 w-1/3 max-w-xs rounded-md bg-muted" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="h-24 rounded-lg bg-muted" />
          <div className="h-24 rounded-lg bg-muted" />
          <div className="h-24 rounded-lg bg-muted" />
          <div className="h-24 rounded-lg bg-muted" />
        </div>
        <div className="h-40 rounded-lg bg-muted" />
      </div>
    </div>
  );
}
