import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LocaleProvider } from "../LocaleProvider";
import { useLocale } from "../useLocale";

function Consumer() {
  const { locale } = useLocale();
  return <span data-testid="locale">{locale}</span>;
}

describe("useLocale", () => {
  afterEach(() => {
    cleanup();
  });

  it("returns the context value when rendered inside a LocaleProvider", () => {
    render(
      <LocaleProvider>
        <Consumer />
      </LocaleProvider>,
    );

    expect(screen.getByTestId("locale")).toBeInTheDocument();
  });

  it("throws when used outside of a LocaleProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);

    expect(() => render(<Consumer />)).toThrow(
      "useLocale must be used within LocaleProvider",
    );

    consoleError.mockRestore();
  });
});
