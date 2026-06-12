import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";

type LanguageToggleProps = {
  locale: Locale;
  onChange: (locale: Locale) => void;
};

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  return (
    <div
      className="language-toggle"
      data-testid="language-toggle"
      role="group"
      aria-label={t(locale, "languageGroupLabel")}
    >
      <button
        type="button"
        className={locale === "en" ? "lang-btn active" : "lang-btn"}
        aria-pressed={locale === "en"}
        onClick={() => { onChange("en"); }}
      >
        EN
      </button>
      <button
        type="button"
        className={locale === "es" ? "lang-btn active" : "lang-btn"}
        aria-pressed={locale === "es"}
        onClick={() => { onChange("es"); }}
      >
        ES
      </button>
    </div>
  );
}
