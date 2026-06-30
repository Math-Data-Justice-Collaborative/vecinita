import { t } from "vecinita-frontend-i18n";

import { useLocale } from "./useLocale";

export interface PaginationControlsProps {
  page: number;
  totalPages: number;
  total: number;
  onPrevious: () => void;
  onNext: () => void;
  previousDisabled?: boolean;
  nextDisabled?: boolean;
}

export function PaginationControls({
  page,
  totalPages,
  total,
  onPrevious,
  onNext,
  previousDisabled = false,
  nextDisabled = false,
}: PaginationControlsProps) {
  const { locale } = useLocale();

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-2"
      data-testid="pagination-controls"
    >
      <p className="text-sm text-muted-foreground">
        {t(locale, "shared.pagination", page, totalPages, total)}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm disabled:opacity-50"
          data-testid="pagination-previous"
          disabled={previousDisabled}
          onClick={onPrevious}
        >
          {t(locale, "shared.previous")}
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm disabled:opacity-50"
          data-testid="pagination-next"
          disabled={nextDisabled}
          onClick={onNext}
        >
          {t(locale, "shared.next")}
        </button>
      </div>
    </div>
  );
}
