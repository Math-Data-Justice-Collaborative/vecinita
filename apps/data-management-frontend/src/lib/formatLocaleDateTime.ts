import type { Locale } from "vecinita-frontend-i18n";

export function formatLocaleDateTime(locale: Locale, value: string): string {
  const tag = locale === "es" ? "es-ES" : "en-US";
  return new Date(value).toLocaleString(tag);
}
