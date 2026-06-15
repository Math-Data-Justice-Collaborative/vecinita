import { t, type Locale } from "vecinita-frontend-i18n";

export interface LanguageToggleProps {
  locale: Locale;
  onChange: (locale: Locale) => void;
}

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  return (
    <div
      className="inline-flex rounded-md border border-border p-0.5"
      data-testid="language-toggle"
      role="group"
      aria-label={t(locale, "shared.languageGroupLabel")}
    >
      <button
        type="button"
        className={
          locale === "en"
            ? "rounded px-2 py-1 text-xs font-medium bg-accent text-accent-foreground"
            : "rounded px-2 py-1 text-xs font-medium text-muted-foreground"
        }
        aria-pressed={locale === "en"}
        onClick={() => {
          onChange("en");
        }}
      >
        EN
      </button>
      <button
        type="button"
        className={
          locale === "es"
            ? "rounded px-2 py-1 text-xs font-medium bg-accent text-accent-foreground"
            : "rounded px-2 py-1 text-xs font-medium text-muted-foreground"
        }
        aria-pressed={locale === "es"}
        onClick={() => {
          onChange("es");
        }}
      >
        ES
      </button>
    </div>
  );
}
