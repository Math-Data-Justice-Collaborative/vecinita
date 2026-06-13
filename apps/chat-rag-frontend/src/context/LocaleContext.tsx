import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { Locale } from "../hooks/useLocale.types";
import {
  detectBrowserLocale,
  readStoredLocale,
} from "../hooks/useLocale.types";

import { LocaleContext } from "./localeContext";

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(
    () => readStoredLocale() ?? detectBrowserLocale(),
  );

  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem("vecinita.locale", next);
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
