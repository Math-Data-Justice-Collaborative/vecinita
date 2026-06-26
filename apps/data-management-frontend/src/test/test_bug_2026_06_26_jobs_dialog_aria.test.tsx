/**
 * BUG-2026-06-26: Radix warns when mobile nav Sheet has Title but no Description.
 *
 * Symptom on production Jobs page: "Missing Description or aria-describedby={undefined}
 * for {DialogContent}" when opening the hamburger menu (Sheet uses Radix Dialog).
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import App from "../App";
import { renderWithProviders } from "./renderWithProviders";

const DIALOG_DESCRIPTION_WARNING =
  /Missing `Description` or `aria-describedby=\{undefined\}` for \{DialogContent\}/;

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("BUG-2026-06-26 jobs dialog aria warning", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("does not warn when opening mobile navigation on the Jobs page", async () => {
    const warnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => undefined);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ jobs: [] })),
    );

    renderWithProviders(
      <MemoryRouter initialEntries={["/jobs"]}>
        <App />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no jobs yet/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /open navigation/i }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const ariaWarnings = warnSpy.mock.calls.filter(([message]) =>
      typeof message === "string"
        ? DIALOG_DESCRIPTION_WARNING.test(message)
        : false,
    );
    expect(ariaWarnings).toHaveLength(0);
  });
});
