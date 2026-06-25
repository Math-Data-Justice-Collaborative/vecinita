import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import App from "../App";

function renderApp(initialRoute = "/dashboard") {
  return renderWithProviders(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Admin navigation", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [] }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders sidebar with all navigation links", () => {
    renderApp();

    const nav = screen.getByTestId("admin-nav");
    expect(nav).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: /dashboard/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /corpus/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /health/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /audit log/i }),
    ).toBeInTheDocument();
  });

  it("navigates to corpus page when clicking Corpus link", async () => {
    renderApp();

    fireEvent.click(screen.getByRole("link", { name: /corpus/i }));
    expect(
      screen.getByText(/ingest urls and manage documents/i),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/no documents in corpus/i)).toBeInTheDocument();
    });
  });

  it("navigates to health page", () => {
    renderApp();

    fireEvent.click(screen.getByRole("link", { name: /health/i }));
    expect(
      screen.getByRole("heading", { name: /health/i, level: 2 }),
    ).toBeInTheDocument();
  });

  it("navigates to audit log page", () => {
    renderApp();

    fireEvent.click(screen.getByRole("link", { name: /audit log/i }));
    expect(screen.getByText(/event history/i)).toBeInTheDocument();
  });

  it("redirects unknown routes to /dashboard", () => {
    renderApp("/unknown-route");

    expect(screen.getByText(/overview of your corpus/i)).toBeInTheDocument();
  });

  it("theme toggle button exists and is clickable", () => {
    renderApp();

    const toggles = screen.getAllByTestId("theme-toggle");
    expect(toggles.length).toBeGreaterThan(0);
    fireEvent.click(toggles[0]);
  });

  it("opens mobile navigation sheet", async () => {
    renderApp();

    fireEvent.click(screen.getByRole("button", { name: /open navigation/i }));
    const sheetTitle = await screen.findAllByText("Vecinita");
    expect(sheetTitle.length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("link", { name: /corpus/i }));
    expect(
      screen.getByText(/ingest urls and manage documents/i),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/no documents in corpus/i)).toBeInTheDocument();
    });
  });
});
