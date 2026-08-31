import { ActionIcon, Tooltip } from "vecinita-frontend-ui";
import { t } from "vecinita-frontend-i18n";

import type { Theme } from "../hooks/useTheme";
import type { Locale } from "../hooks/useLocale.types";

type ThemeToggleProps = {
  theme: Theme;
  locale: Locale;
  onToggle: () => void;
};

/** Light/dark switch for the sidebar (D8). Shows the icon/label of the theme
 *  the user would switch *to*. */
export function ThemeToggle({ theme, locale, onToggle }: ThemeToggleProps) {
  const goingDark = theme === "light";
  const label = t(
    locale,
    goingDark ? "chat.switchToDark" : "chat.switchToLight",
  );

  return (
    <Tooltip content={t(locale, "shared.tooltip.themeToggle")}>
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
          {t(locale, "chat.themeToggleLabel")}
        </span>
      </button>
    </Tooltip>
  );
}
