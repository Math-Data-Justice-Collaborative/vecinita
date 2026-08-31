import { Tooltip } from "vecinita-frontend-ui";
import { t } from "vecinita-frontend-i18n";

import type { Locale } from "../hooks/useLocale.types";

type LanguageToggleProps = {
  locale: Locale;
  onChange: (locale: Locale) => void;
};

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  return (
    <Tooltip content={t(locale, "shared.tooltip.languageToggle")}>
      <div
        className="language-toggle"
        data-testid="language-toggle"
        role="group"
        aria-label={t(locale, "shared.languageGroupLabel")}
        tabIndex={0}
      >
        <button
          type="button"
          className={locale === "en" ? "lang-btn active" : "lang-btn"}
          aria-pressed={locale === "en"}
          onClick={() => {
            onChange("en");
          }}
        >
          EN
        </button>
        <button
          type="button"
          className={locale === "es" ? "lang-btn active" : "lang-btn"}
          aria-pressed={locale === "es"}
          onClick={() => {
            onChange("es");
          }}
        >
          ES
        </button>
      </div>
    </Tooltip>
  );
}
