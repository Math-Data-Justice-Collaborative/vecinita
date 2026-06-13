import { cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/hooks/useTheme";

function ThemeReader() {
  const { theme } = useTheme();
  return <span data-testid="current-theme">{theme}</span>;
}

describe("ThemeProvider and ThemeToggle", () => {
  afterEach(() => {
    cleanup();
    localStorage.clear();
    vi.restoreAllMocks();
    document.documentElement.classList.remove("light", "dark");
  });

  it("defaults to system theme when storage is empty", () => {
    render(
      <ThemeProvider>
        <ThemeReader />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("system");
  });

  it("reads stored dark theme from localStorage", () => {
    localStorage.setItem("vecinita-ui-theme", "dark");
    render(
      <ThemeProvider>
        <ThemeReader />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("applies light theme class", () => {
    localStorage.setItem("vecinita-ui-theme", "light");
    render(
      <ThemeProvider>
        <ThemeReader />
      </ThemeProvider>,
    );
    expect(document.documentElement.classList.contains("light")).toBe(true);
  });

  it("follows system preference when theme is system", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("dark"),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    );

    render(
      <ThemeProvider>
        <ThemeReader />
      </ThemeProvider>,
    );

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("cycles dark → light → system → dark via ThemeToggle", () => {
    localStorage.setItem("vecinita-ui-theme", "dark");
    render(
      <ThemeProvider>
        <ThemeToggle />
        <ThemeReader />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByTestId("current-theme")).toHaveTextContent("light");

    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByTestId("current-theme")).toHaveTextContent("system");

    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
  });

  it("throws when useTheme is used outside ThemeProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    expect(() => renderHook(() => useTheme())).toThrow(/ThemeProvider/i);
    consoleError.mockRestore();
  });
});
