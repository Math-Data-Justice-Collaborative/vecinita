import { ActionIcon, Tooltip } from "vecinita-frontend-ui";
import { t as i18nT } from "vecinita-frontend-i18n";

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
    <Tooltip content={i18nT(locale, "shared.tooltip.themeToggle")}>
      <button
        type="button"
        className="theme-toggle"
        data-testid="theme-toggle"
        aria-label={label}
        onClick={onToggle}
      >
        <ActionIcon
          motion="press"
          pending={false}
          className="theme-toggle-icon"
          data-testid="theme-toggle-icon"
        >
          <span aria-hidden="true">{goingDark ? "🌙" : "☀️"}</span>
        </ActionIcon>
        <span className="theme-toggle-text">
          {t(locale, "themeToggleLabel")}
        </span>
      </button>
    </Tooltip>
  );
}
