import { useContext } from "react";

import {
  LocaleContext,
  type LocaleContextValue,
} from "../context/localeContext";

export type { Locale } from "./useLocale.types";

export { detectBrowserLocale, readStoredLocale } from "./useLocale.types";

export function useLocale(): LocaleContextValue {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useLocale must be used within LocaleProvider");
  }
  return context;
}
