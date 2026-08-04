import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./ThemeToggle";
import { renderWithLocale } from "../test/renderWithLocale";

describe("ThemeToggle", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows the dark-mode affordance when the current theme is light", () => {
    const onToggle = vi.fn();
    renderWithLocale(
      <ThemeToggle theme="light" locale="en" onToggle={onToggle} />,
    );

    const button = screen.getByTestId("theme-toggle");
    expect(button).toHaveAttribute(
      "aria-label",
      expect.stringMatching(/dark/i),
    );
    expect(button).toHaveTextContent("🌙");

    fireEvent.click(button);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("shows the light-mode affordance when the current theme is dark", () => {
    renderWithLocale(
      <ThemeToggle theme="dark" locale="en" onToggle={() => {}} />,
    );

    const button = screen.getByTestId("theme-toggle");
    expect(button).toHaveAttribute(
      "aria-label",
      expect.stringMatching(/light/i),
    );
    expect(button).toHaveTextContent("☀️");
  });
});
