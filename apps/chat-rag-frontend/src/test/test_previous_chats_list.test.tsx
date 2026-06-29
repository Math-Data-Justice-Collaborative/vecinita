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
import { deriveConversationLabel } from "../components/previousChatsLabel";
import type { Conversation } from "../hooks/useConversationStore";

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
  'data: {"token":"An "}\n\n' +
  'data: {"token":"answer."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true}\n\n';

async function ask(question: string): Promise<void> {
  fireEvent.change(screen.getByLabelText(/your question/i), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  await screen.findByText(question);
  await waitFor(() => {
    expect(screen.getByText(/An answer\./)).toBeInTheDocument();
  });
}

function expandPreviousChats(): void {
  const toggle = screen.getByRole("button", { name: /previous chats/i });
  if (toggle.getAttribute("aria-expanded") !== "true") {
    fireEvent.click(toggle);
  }
}

describe("F33 — previous-chats list (UJ-025)", () => {
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

  it('shows "no previous chats" before anything is archived', () => {
    render(<App />);
    expandPreviousChats();
    expect(screen.getByText(/no previous chats yet/i)).toBeInTheDocument();
  });

  it('"New chat" archives the active conversation with a label + relative time, then empties it (TC-074)', async () => {
    render(<App />);
    await ask("Where is the food pantry?");

    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));

    // Active conversation is now empty.
    expect(screen.getByText(/ask a question in english/i)).toBeInTheDocument();

    expandPreviousChats();
    const item = within(screen.getByTestId("previous-chats-list")).getByText(
      /where is the food pantry\?/i,
    );
    expect(item).toBeInTheDocument();
    const listItem = screen.getByTestId("previous-chats-list");
    expect(listItem.querySelector(".previous-chat-time")?.textContent).toMatch(
      /now|ago|second/i,
    );
  });

  it("restores a selected conversation, deletes one, and clears all (TC-076, R47)", async () => {
    render(<App />);
    await ask("First question?");
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    await ask("Second question?");
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));

    expandPreviousChats();
    const list = screen.getByTestId("previous-chats-list");
    expect(within(list).getByText(/first question\?/i)).toBeInTheDocument();
    expect(within(list).getByText(/second question\?/i)).toBeInTheDocument();

    // Select the older conversation — it becomes active.
    fireEvent.click(within(list).getByText(/first question\?/i));
    expect(screen.getByTestId("message-list").textContent).toMatch(
      /first question\?/i,
    );

    // Delete the remaining archived conversation.
    expandPreviousChats();
    const remaining = screen.getByTestId("previous-chats-list");
    fireEvent.click(
      within(remaining).getByRole("button", { name: /delete conversation/i }),
    );
    expect(
      within(screen.getByTestId("previous-chats")).queryByText(
        /second question\?/i,
      ),
    ).not.toBeInTheDocument();

    // Archive again, then clear all history.
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    expandPreviousChats();
    fireEvent.click(screen.getByRole("button", { name: /clear all history/i }));
    expandPreviousChats();
    expect(screen.getByText(/no previous chats yet/i)).toBeInTheDocument();
  });

  it('"Clear" resets only the active conversation (TC-076)', async () => {
    render(<App />);
    await ask("Clear me?");
    fireEvent.click(screen.getByRole("button", { name: /clear history/i }));
    expect(screen.getByText(/ask a question in english/i)).toBeInTheDocument();
  });

  it("caps the previous-chats list at 10 and evicts the oldest through the UI (TC-075, R45)", async () => {
    render(<App />);

    // Archive 11 conversations via repeated ask → "New chat".
    for (let i = 0; i <= 10; i++) {
      await ask(`conversation ${String(i)}?`);
      fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    }

    expandPreviousChats();
    const list = screen.getByTestId("previous-chats-list");

    // Exactly the last 10 remain, newest first; the toggle reflects the count.
    expect(within(list).getAllByRole("listitem")).toHaveLength(10);
    expect(
      screen.getByRole("button", { name: /previous chats/i }).textContent,
    ).toContain("(10)");
    expect(within(list).getByText(/conversation 10\?/i)).toBeInTheDocument();
    // The very first conversation was evicted (FIFO).
    expect(
      within(list).queryByText(/conversation 0\?/i),
    ).not.toBeInTheDocument();
  });

  it("restores a previous conversation's sources, not just its text (TC-076, AC-S5)", async () => {
    const sourceSse =
      'data: {"token":"Housing answer."}\n\n' +
      'data: {"sources":[{"chunk_id":"c1","document_id":"d1","title":"Housing aid","url":"https://example.com","score":0.9}]}\n\n' +
      'data: {"done":true}\n\n';
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          return Promise.resolve(sseResponse(sourceSse));
        }
        return Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        );
      }),
    );

    render(<App />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Where is housing aid?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    await screen.findByText("Where is housing aid?");
    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /housing aid/i }),
      ).toBeInTheDocument();
    });

    // Archive it; the source link leaves the active view.
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    expect(
      screen.queryByRole("link", { name: /housing aid/i }),
    ).not.toBeInTheDocument();

    // Restore it from the previous-chats list.
    expandPreviousChats();
    fireEvent.click(
      within(screen.getByTestId("previous-chats-list")).getByText(
        /where is housing aid\?/i,
      ),
    );

    // Both the message text AND its restored sources render.
    expect(
      within(screen.getByTestId("message-list")).getByText(
        "Where is housing aid?",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /housing aid/i }),
    ).toBeInTheDocument();
  });
});

describe("deriveConversationLabel", () => {
  function conv(messages: Conversation["messages"]): Conversation {
    return { id: "x", messages, createdAt: 0 };
  }

  it("uses the first user message", () => {
    expect(
      deriveConversationLabel(
        conv([
          { id: "u", role: "user", content: "How do I apply for housing?" },
          { id: "a", role: "assistant", content: "..." },
        ]),
      ),
    ).toBe("How do I apply for housing?");
  });

  it("truncates to 60 characters", () => {
    const long = "a".repeat(80);
    const label = deriveConversationLabel(
      conv([{ id: "u", role: "user", content: long }]),
    );
    expect(label).toBe(`${"a".repeat(60)}…`);
  });

  it("returns an empty label when there is no user message", () => {
    expect(
      deriveConversationLabel(
        conv([{ id: "a", role: "assistant", content: "orphan" }]),
      ),
    ).toBe("");
  });
});
