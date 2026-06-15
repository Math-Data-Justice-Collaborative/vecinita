import { useCallback } from "react";
import { t, type StringMessageKey } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

export function useAdminT() {
  const { locale } = useLocale();
  return useCallback(
    (key: StringMessageKey, params?: Record<string, string | number>) =>
      t(locale, key, params),
    [locale],
  );
}
