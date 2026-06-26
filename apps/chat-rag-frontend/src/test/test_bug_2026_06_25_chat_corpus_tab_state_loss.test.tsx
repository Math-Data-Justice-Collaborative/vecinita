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

/**
 * BUG-2026-06-25 / issue #53 — chat history must survive Chat → Corpus → Chat
 * navigation. Previously `useChatHistory` lived inside `ChatPanel`, which is
 * unmounted on Corpus navigation, discarding the conversation.
 */
describe("BUG-2026-06-25 — chat survives the Corpus tab round-trip (#53)", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("vecinita.locale", "en");
    window.history.replaceState({}, "", "/");

    const askSse =
      'data: {"token":"Local "}\n\n' +
      'data: {"token":"aid info."}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          return Promise.resolve(sseResponse(askSse));
        }
        if (url.includes("/api/v1/documents")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({ items: [], page: 1, page_size: 20, total: 0 }),
              { status: 200 },
            ),
          );
        }
        // /api/v1/tags and /api/v1/warm
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

  it("preserves the conversation after navigating to Corpus and back", async () => {
    const question = "Where can I find legal aid?";
    render(<App />);

    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: question },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    // Conversation is shown in the chat panel.
    expect(await screen.findByText(question)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Local aid info\./)).toBeInTheDocument();
    });

    // Navigate to the Corpus tab.
    fireEvent.click(screen.getByRole("button", { name: /^corpus$/i }));
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();

    // Navigate back to Chat.
    fireEvent.click(screen.getByRole("button", { name: /^chat$/i }));

    // The conversation must still be there (regression: it was wiped).
    expect(screen.getByLabelText(/your question/i)).toBeInTheDocument();
    expect(screen.getByText(question)).toBeInTheDocument();
    expect(screen.getByText(/Local aid info\./)).toBeInTheDocument();
    expect(screen.queryByText(/ask a question in english/i)).not.toBeInTheDocument();
  });
});
