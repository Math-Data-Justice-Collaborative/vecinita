import { createContext } from "react";

import type { Locale } from "vecinita-frontend-i18n";

export interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const LocaleContext = createContext<LocaleContextValue | null>(null);
