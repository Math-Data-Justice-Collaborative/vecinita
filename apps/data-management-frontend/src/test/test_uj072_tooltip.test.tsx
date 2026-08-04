import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { t } from "vecinita-frontend-i18n";

import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";
import { renderWithProviders } from "./renderWithProviders";

describe("UJ-072 / F67 Tooltip wiring (admin ThemeToggle)", () => {
  afterEach(() => {
    cleanup();
  });

  it("TC-223: theme tooltip shows English content on focus", async () => {
    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <ThemeToggle />
        </MemoryRouter>
      </ThemeProvider>,
    );

    const trigger = screen.getByTestId("theme-toggle");
    trigger.focus();
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toHaveTextContent(
        t("en", "shared.tooltip.themeToggle"),
      );
    });
  });

  it("TC-224: theme tooltip appears on keyboard focus without hover", async () => {
    renderWithProviders(
      <ThemeProvider>
        <MemoryRouter>
          <ThemeToggle />
        </MemoryRouter>
      </ThemeProvider>,
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
