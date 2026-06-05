import { useCallback, useState } from "react";

export type Locale = "en" | "es";

const STORAGE_KEY = "vecinita.locale";

export function detectBrowserLocale(): Locale {
  const lang = navigator.language.toLowerCase();
  return lang.startsWith("es") ? "es" : "en";
}

export function readStoredLocale(): Locale | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "es") {
    return stored;
  }
  return null;
}

export function useLocale(): { locale: Locale; setLocale: (next: Locale) => void } {
  const [locale, setLocaleState] = useState<Locale>(
    () => readStoredLocale() ?? detectBrowserLocale(),
  );

  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem(STORAGE_KEY, next);
    setLocaleState(next);
  }, []);

  return { locale, setLocale };
}
