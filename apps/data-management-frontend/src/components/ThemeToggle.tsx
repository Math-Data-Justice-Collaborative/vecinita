import { Moon, Sun } from "lucide-react";
import { t } from "vecinita-frontend-i18n";
import { ActionIcon, Tooltip, useLocale } from "vecinita-frontend-ui";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { locale } = useLocale();

  const toggleTheme = () => {
    if (theme === "dark") {
      setTheme("light");
    } else if (theme === "light") {
      setTheme("system");
    } else {
      setTheme("dark");
    }
  };

  return (
    <Tooltip content={t(locale, "shared.tooltip.themeToggle")}>
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleTheme}
        aria-label={t(locale, "admin.theme.toggle")}
        data-testid="theme-toggle"
      >
        <ActionIcon
          motion="press"
          pending={false}
          data-testid="theme-toggle-icon"
        >
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </ActionIcon>
      </Button>
    </Tooltip>
  );
}
