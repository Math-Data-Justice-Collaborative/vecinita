import type { Theme } from "../hooks/useTheme";
import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";

type ThemeToggleProps = {
  theme: Theme;
  locale: Locale;
  onToggle: () => void;
};

/** Light/dark switch for the sidebar (D8). Shows the icon/label of the theme
 *  the user would switch *to*. */
export function ThemeToggle({ theme, locale, onToggle }: ThemeToggleProps) {
  const goingDark = theme === "light";
  const label = t(locale, goingDark ? "switchToDark" : "switchToLight");

  return (
    <button
      type="button"
      className="theme-toggle"
      data-testid="theme-toggle"
      aria-label={label}
      title={label}
      onClick={onToggle}
    >
      <span aria-hidden="true" className="theme-toggle-icon">
        {goingDark ? "🌙" : "☀️"}
      </span>
      <span className="theme-toggle-text">{t(locale, "themeToggleLabel")}</span>
    </button>
  );
}
