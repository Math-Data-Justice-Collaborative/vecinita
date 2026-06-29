import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { LOCALE_STORAGE_KEY } from "vecinita-frontend-i18n";

import { LocaleProvider } from "../LocaleProvider";
import { useLocale } from "../useLocale";

function LocaleProbe() {
  const { locale, setLocale } = useLocale();
  return (
    <div>
      <span data-testid="current-locale">{locale}</span>
      <button
        type="button"
        onClick={() => {
          setLocale("en");
        }}
      >
        set-en
      </button>
      <button
        type="button"
        onClick={() => {
          setLocale("es");
        }}
      >
        set-es
      </button>
    </div>
  );
}

describe("LocaleProvider", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    localStorage.clear();
  });

  it("initializes from the stored locale and reflects it on the document element", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "en");

    render(
      <LocaleProvider>
        <LocaleProbe />
      </LocaleProvider>,
    );

    expect(screen.getByTestId("current-locale")).toHaveTextContent("en");
    expect(document.documentElement.lang).toBe("en");
  });

  it("persists and applies a new locale when setLocale is called", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "en");

    render(
      <LocaleProvider>
        <LocaleProbe />
      </LocaleProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "set-es" }));

    expect(screen.getByTestId("current-locale")).toHaveTextContent("es");
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("es");
    expect(document.documentElement.lang).toBe("es");
  });
});
