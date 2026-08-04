import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ACTION_ICON_MOTION_CLASS } from "vecinita-frontend-ui";

import { ChatPanel } from "../components/ChatPanel";
import { renderWithLocale } from "./renderWithLocale";

function hangingStream(): Response {
  const stream = new ReadableStream({
    start() {
      /* leave open so Ask stays pending */
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

describe("UJ-071 / F66 ActionIcon wiring (ChatRAG Ask)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("TC-221: ask icon pulses with aria-busy while streaming", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input.toString();
      if (url.includes("/api/v1/warm")) {
        return Promise.resolve(
          new Response(JSON.stringify({ status: "warming" }), { status: 200 }),
        );
      }
      if (url.includes("/api/v1/tags")) {
        return Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        );
      }
      if (url.includes("/api/v1/ask/stream")) {
        return Promise.resolve(hangingStream());
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithLocale(<ChatPanel />);

    const input = screen.getByLabelText(/your question|tu pregunta/i);
    fireEvent.change(input, { target: { value: "What is justice?" } });
    fireEvent.click(screen.getByTestId("chat-ask-submit"));

    await waitFor(() => {
      const icon = screen.getByTestId("chat-ask-icon");
      expect(icon).toHaveAttribute("aria-busy", "true");
      expect(icon.className).toContain(ACTION_ICON_MOTION_CLASS.pulse);
    });
  });
});
