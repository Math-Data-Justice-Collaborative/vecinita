import { Tooltip } from "vecinita-frontend-ui";
import { t as i18nT } from "vecinita-frontend-i18n";

import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";

type LanguageToggleProps = {
  locale: Locale;
  onChange: (locale: Locale) => void;
};

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  return (
    <Tooltip content={i18nT(locale, "shared.tooltip.languageToggle")}>
      <div
        className="language-toggle"
        data-testid="language-toggle"
        role="group"
        aria-label={t(locale, "languageGroupLabel")}
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
