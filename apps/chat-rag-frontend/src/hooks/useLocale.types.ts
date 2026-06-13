export type Locale = "en" | "es";

const STORAGE_KEY = "vecinita.locale";

export function detectBrowserLocale(): Locale {
  const lang = navigator.language.toLowerCase();
  if (lang.startsWith("es")) {
    return "es";
  }
  if (lang.startsWith("en")) {
    return "en";
  }
  return "es";
}

export function readStoredLocale(): Locale | null {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "es") {
    return stored;
  }
  return null;
}
