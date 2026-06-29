import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

/** Device-local theme preference (D8/A5). Stored only in `localStorage`, never
 *  sent to the server — consistent with Vecinita's zero-personal-data posture. */
export const THEME_STORAGE_KEY = "vecinita.theme.v1";

/** ChatGPT-style default: dark. */
const DEFAULT_THEME: Theme = "dark";

function readStoredTheme(): Theme | null {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  } catch {
    // Storage disabled/unavailable: fall back to the default, in-memory only.
  }
  return null;
}

function applyTheme(theme: Theme): void {
  // `document` is always defined in the browser/jsdom; the guard only protects
  // against a non-DOM (SSR) import and is not exercised under test.
  /* v8 ignore next */
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", theme);
  }
}

/**
 * Light/dark theme with device-local persistence. Applies `data-theme` to the
 * document root so CSS variables switch, and degrades to in-memory state when
 * `localStorage` is unavailable (mirrors the chat-history fallback, TC-073).
 */
export function useTheme(): {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
} {
  const [theme, setThemeState] = useState<Theme>(
    () => readStoredTheme() ?? DEFAULT_THEME,
  );

  useEffect(() => {
    applyTheme(theme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Persistence disabled this session; theme still applies in-memory.
    }
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((current) => (current === "dark" ? "light" : "dark"));
  }, []);

  return { theme, toggleTheme, setTheme };
}
