import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  detectBrowserLocale,
  readStoredLocale,
  LOCALE_STORAGE_KEY,
  type Locale,
} from "vecinita-frontend-i18n";

import { LocaleContext } from "./localeContext";

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(
    () => readStoredLocale() ?? detectBrowserLocale(),
  );

  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem(LOCALE_STORAGE_KEY, next);
    setLocaleState(next);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale]);

  return (
    <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
  );
}
