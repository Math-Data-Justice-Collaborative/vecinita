import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import {
  detectBrowserLocale,
  readStoredLocale,
} from "../hooks/useLocale.types";

describe("BUG-2026-06-05 — ChatRAG language toggle UI (EV-005 #57)", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        ),
      ),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("places a single language toggle in the persistent sidebar chrome", () => {
    // Post-redesign (S003 ChatGPT-style layout) the toggle lives in the always-
    // mounted sidebar rather than the top header. The BUG-2026-06-05 invariant
    // still holds: exactly one toggle, and never buried inside the chat panel.
    render(<App />);

    const sidebar = screen.getByTestId("sidebar");
    expect(
      sidebar.querySelector('[data-testid="language-toggle"]'),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("group", { name: /language/i })).toHaveLength(1);
    expect(
      document.querySelector(".chat-panel .language-toggle"),
    ).not.toBeInTheDocument();
  });

  it("translates chat UI chrome when locale is Spanish", () => {
    localStorage.setItem("vecinita.locale", "es");
    render(<App />);

    expect(
      screen.getByRole("button", { name: /^preguntar$/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/tu pregunta/i)).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: /primary/i }),
    ).toHaveTextContent(/chat/i);
    expect(
      screen.getByText(/pregunta en inglés o español/i),
    ).toBeInTheDocument();
  });

  it("defaults to Spanish when browser language is neither English nor Spanish", () => {
    vi.stubGlobal("navigator", { language: "fr-FR" });
    expect(readStoredLocale()).toBeNull();
    expect(detectBrowserLocale()).toBe("es");
  });

  it("switches visible UI strings when user selects ES in the header toggle", () => {
    localStorage.setItem("vecinita.locale", "en");
    render(<App />);

    expect(screen.getByRole("button", { name: /^ask$/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));

    expect(
      screen.getByRole("button", { name: /^preguntar$/i }),
    ).toBeInTheDocument();
  });

  it("syncs document.documentElement.lang with the active locale", () => {
    localStorage.setItem("vecinita.locale", "es");
    render(<App />);
    expect(document.documentElement.lang).toBe("es");

    fireEvent.click(screen.getByRole("button", { name: /^en$/i }));
    expect(document.documentElement.lang).toBe("en");
  });
});
