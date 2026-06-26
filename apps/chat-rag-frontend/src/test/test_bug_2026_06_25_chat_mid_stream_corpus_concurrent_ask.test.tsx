import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
  type Mock,
} from "vitest";

import App from "../App";

/**
 * BUG-2026-06-25 — mid-stream Corpus tab switch must not lose the in-flight ask
 * state. The #53 fix lifted the conversation history into the always-mounted
 * shell, but `loading` stayed local to `ChatPanel`. Switching to Corpus while a
 * stream is in flight and returning previously reset `loading` to `false`,
 * re-enabling Ask and allowing a concurrent stream against the shared history.
 */
describe("BUG-2026-06-25 — in-flight ask survives the Corpus tab round-trip", () => {
  let streamFetch: Mock<() => Promise<Response>>;

  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("vecinita.locale", "en");
    window.history.replaceState({}, "", "/");

    // ask/stream never resolves → the stream stays in flight (loading stays true).
    streamFetch = vi.fn<() => Promise<Response>>(
      () => new Promise<Response>(() => {}),
    );

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          return streamFetch();
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

  it("keeps Ask disabled and does not start a concurrent stream after a mid-stream Corpus round-trip", async () => {
    const question = "Where can I find legal aid?";
    render(<App />);

    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: question },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    // Stream is in flight: the user message is shown and Ask switches to "Asking".
    expect(await screen.findByText(question)).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: /asking/i }),
    ).toBeDisabled();
    expect(streamFetch).toHaveBeenCalledTimes(1);

    // Navigate to the Corpus tab mid-stream.
    fireEvent.click(screen.getByRole("button", { name: /^corpus$/i }));
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();

    // Navigate back to Chat before the stream completes.
    fireEvent.click(screen.getByRole("button", { name: /^chat$/i }));

    // The in-flight ask state must be preserved: Ask is still "Asking" and
    // disabled, so a second concurrent stream cannot be started.
    expect(screen.getByRole("button", { name: /asking/i })).toBeDisabled();
    expect(streamFetch).toHaveBeenCalledTimes(1);

    // The original conversation is still present.
    expect(screen.getByText(question)).toBeInTheDocument();
  });
});
