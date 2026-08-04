import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { t } from "vecinita-frontend-i18n";

import { ThemeToggle } from "../components/ThemeToggle";
import { renderWithLocale } from "./renderWithLocale";

describe("UJ-072 / F67 Tooltip wiring (ChatRAG ThemeToggle)", () => {
  afterEach(() => {
    cleanup();
  });

  it("TC-223: theme tooltip shows English then Spanish after locale change", async () => {
    const { rerender } = renderWithLocale(
      <ThemeToggle theme="light" locale="en" onToggle={() => undefined} />,
    );

    const trigger = screen.getByTestId("theme-toggle");
    trigger.focus();
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toHaveTextContent(
        t("en", "shared.tooltip.themeToggle"),
      );
    });

    rerender(
      <ThemeToggle theme="light" locale="es" onToggle={() => undefined} />,
    );
    const esTrigger = screen.getByTestId("theme-toggle");
    esTrigger.focus();
    fireEvent.focus(esTrigger);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toHaveTextContent(
        t("es", "shared.tooltip.themeToggle"),
      );
    });
  });

  it("TC-224: theme tooltip appears on keyboard focus", async () => {
    renderWithLocale(
      <ThemeToggle theme="dark" locale="en" onToggle={() => undefined} />,
    );

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    const trigger = screen.getByTestId("theme-toggle");
    trigger.focus();
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
    });
  });
});
