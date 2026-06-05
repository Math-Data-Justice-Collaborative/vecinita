import type { Locale } from "../hooks/useLocale";

type LanguageToggleProps = {
  locale: Locale;
  onChange: (locale: Locale) => void;
};

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  return (
    <div className="language-toggle" role="group" aria-label="Language">
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
