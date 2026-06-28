import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";

function sseResponse(body: string): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

const askSse =
  'data: {"token":"Reply."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

/**
 * AC-S6 (F33, ADR-004/023/025): chat history is device-only. It is never sent
 * to the server (no history in the ask payload), and is persisted only to
 * device-local `localStorage` — never transmitted off the device. Per ADR-025
 * the store uses `localStorage` (persists across tab close, shared across tabs
 * of the same origin) rather than `sessionStorage`.
 */
describe("F33 — chat history stays device-only (AC-S6)", () => {
  const askBodies: string[] = [];

  beforeEach(() => {
    askBodies.length = 0;
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem("vecinita.locale", "en");
    window.history.replaceState({}, "", "/");
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          askBodies.push(typeof init?.body === "string" ? init.body : "");
          return Promise.resolve(sseResponse(askSse));
        }
        return Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        );
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    window.history.replaceState({}, "", "/");
  });

  async function ask(question: string): Promise<void> {
    const repliesBefore = screen.queryAllByText(/Reply\./).length;
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: question },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    await screen.findByText(question);
    await waitFor(() => {
      expect(screen.getAllByText(/Reply\./)).toHaveLength(repliesBefore + 1);
    });
  }

  it("never includes prior conversation history in the ask payload", async () => {
    render(<App />);
    await ask("First private question?");
    await ask("Second private question?");

    expect(askBodies).toHaveLength(2);
    for (const body of askBodies) {
      const parsed = JSON.parse(body) as Record<string, unknown>;
      // Only the current question + language — no messages/history/conversation.
      expect(Object.keys(parsed).sort()).toEqual(["language", "question"]);
    }
    // The second request must not carry the first turn's text.
    expect(askBodies[1]).not.toContain("First private question?");
  });

  it("persists history to device-local localStorage, never sessionStorage/cookies", async () => {
    render(<App />);
    await ask("Where do I store this?");

    // Persisted to localStorage so it survives a tab close and is shared with
    // other tabs of the same origin (ADR-025).
    const stored = localStorage.getItem("vecinita.chat.history.v1");
    expect(stored).not.toBeNull();
    expect(stored).toContain("Where do I store this?");

    // Not written to sessionStorage or cookies, and never leaves the device.
    expect(sessionStorage.getItem("vecinita.chat.history.v1")).toBeNull();
    const sessionValues = Object.keys(sessionStorage).map(
      (key) => sessionStorage.getItem(key) ?? "",
    );
    expect(
      sessionValues.some((value) => value.includes("Where do I store this?")),
    ).toBe(false);
    expect(document.cookie).not.toContain("Where do I store this?");
  });
});
