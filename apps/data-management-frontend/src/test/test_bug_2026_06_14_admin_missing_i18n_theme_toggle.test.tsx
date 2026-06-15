import { cleanup, render, screen } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import App from "../App";

function renderAdmin(route = "/dashboard") {
  return renderWithProviders(
    <MemoryRouter initialEntries={[route]}>
      <App />
    </MemoryRouter>,
  );
}

describe("BUG-2026-06-14 — Admin missing i18n toggle and inconsistent theme chrome", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [] }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("exposes language toggle in admin layout chrome (regression for missing F31 toggle)", () => {
    renderAdmin("/corpus");
    expect(screen.getByTestId("language-toggle")).toBeInTheDocument();
  });

  it("exposes theme toggle on corpus route without opening mobile nav sheet", () => {
    renderAdmin("/corpus");
    expect(screen.getByTestId("theme-toggle")).toBeInTheDocument();
  });
});
