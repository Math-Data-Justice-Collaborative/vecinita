export type Locale = "en" | "es";

export const LOCALE_STORAGE_KEY = "vecinita.locale";

export function detectBrowserLocale(): Locale {
  const lang = navigator.language.toLowerCase();
  if (lang.startsWith("es")) {
    return "es";
  }
  if (lang.startsWith("en")) {
    return "en";
  }
  // Spanish-first default: Vecinita serves a primarily Spanish-speaking
  // community, so browsers reporting neither es nor en fall back to es. The
  // admin UI shares this default but always exposes the EN/ES toggle, and an
  // explicit choice is persisted via readStoredLocale().
  return "es";
}

export function readStoredLocale(): Locale | null {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (stored === "en" || stored === "es") {
    return stored;
  }
  return null;
}
