import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import {
  CHAT_HISTORY_STORAGE_KEY,
  type Conversation,
} from "../hooks/useConversationStore";

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
  'data: {"token":"Full "}\n\n' +
  'data: {"token":"Vecinita answer."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

describe("BUG-2026-07-25 previous chats empty assistant (#145)", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem("vecinita.locale", "en");
    window.history.replaceState({}, "", "/");
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
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

  it("restores non-empty assistant content after New chat → select", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Where is the clinic?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    await screen.findByText("Where is the clinic?");
    await waitFor(() => {
      expect(screen.getByText(/Full Vecinita answer\./)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));

    const toggle = screen.getByRole("button", { name: /previous chats/i });
    if (toggle.getAttribute("aria-expanded") !== "true") {
      fireEvent.click(toggle);
    }
    fireEvent.click(
      within(screen.getByTestId("previous-chats-list")).getByText(
        /where is the clinic\?/i,
      ),
    );

    const list = screen.getByTestId("message-list");
    expect(within(list).getByText("Where is the clinic?")).toBeInTheDocument();
    expect(
      within(list).getByText(/Full Vecinita answer\./),
    ).toBeInTheDocument();
  });

  it("persists non-empty assistant content into localStorage on archive", async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Persist me?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    await waitFor(() => {
      expect(screen.getByText(/Full Vecinita answer\./)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));

    const raw = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw ?? "{}") as {
      previous: Conversation[];
    };
    const archived = parsed.previous[0];
    expect(archived).toBeDefined();
    const assistant = archived?.messages.find((m) => m.role === "assistant");
    expect(assistant?.content).toBe("Full Vecinita answer.");
  });

  it("disables previous-chat select while an ask stream is in flight (#145)", async () => {
    localStorage.setItem(
      CHAT_HISTORY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        active: {
          id: "active-empty",
          messages: [],
          createdAt: Date.now(),
        },
        previous: [
          {
            id: "prior-conv-id",
            createdAt: Date.now() - 60_000,
            messages: [
              { id: "u0", role: "user", content: "Prior completed question?" },
              { id: "a0", role: "assistant", content: "Prior answer." },
            ],
          },
        ],
      }),
    );

    let releaseStream: ((value: Response) => void) | undefined;
    const pendingStream = new Promise<Response>((resolve) => {
      releaseStream = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          return pendingStream;
        }
        return Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        );
      }),
    );

    render(<App />);

    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Interrupted mid-stream?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    await screen.findByRole("button", { name: /asking/i });

    const toggle = screen.getByRole("button", { name: /previous chats/i });
    if (toggle.getAttribute("aria-expanded") !== "true") {
      fireEvent.click(toggle);
    }
    expect(
      within(screen.getByTestId("previous-chats-list")).getByRole("button", {
        name: /prior completed question\?/i,
      }),
    ).toBeDisabled();

    releaseStream?.(sseResponse(askSse));
    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /asking/i }),
      ).not.toBeInTheDocument();
    });
  });
});
