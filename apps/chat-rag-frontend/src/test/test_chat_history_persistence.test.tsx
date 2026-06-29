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
  'data: {"token":"Local "}\n\n' +
  'data: {"token":"aid info."}\n\n' +
  'data: {"sources":[{"chunk_id":"c1","document_id":"d1","title":"Legal aid","url":"https://example.com","score":0.9}]}\n\n' +
  'data: {"done":true}\n\n';

function stubFetch() {
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
}

/** Ask one question and wait for its streamed answer to settle. */
async function ask(question: string): Promise<void> {
  const answersBefore = screen.queryAllByText(/Local aid info\./).length;
  fireEvent.change(screen.getByLabelText(/your question/i), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
  await screen.findByText(question);
  await waitFor(() => {
    expect(screen.queryAllByText(/Local aid info\./)).toHaveLength(
      answersBefore + 1,
    );
  });
}

/**
 * F33 / UJ-024 — the active conversation is persisted to device-local
 * `localStorage` (ADR-025) and rehydrated after a page reload (modeled here as
 * an `App` unmount + remount sharing the same jsdom `localStorage`). Because it
 * is `localStorage`, it also survives a tab close and is shared with new tabs.
 */
describe("F33 — chat history persists across refresh / tab-away (UJ-024)", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.setItem("vecinita.locale", "en");
    window.history.replaceState({}, "", "/");
    stubFetch();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    window.history.replaceState({}, "", "/");
  });

  it("rehydrates the conversation and its sources after a remount (TC-072)", async () => {
    const question = "Where can I find legal aid?";
    const firstRender = render(<App />);

    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: question },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(await screen.findByText(question)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Local aid info\./)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByTestId("source-list")).toBeInTheDocument();
    });

    // Simulate a page reload: tear the app down and mount a fresh instance that
    // shares the same jsdom `localStorage`.
    firstRender.unmount();
    render(<App />);

    expect(screen.getByText(question)).toBeInTheDocument();
    expect(screen.getByText(/Local aid info\./)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /legal aid/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/ask a question in english/i),
    ).not.toBeInTheDocument();
  });

  it("continues a rehydrated conversation and re-persists the new turn (UJ-024 step 4)", async () => {
    const firstRender = render(<App />);
    await ask("First question after reload?");

    // First reload: the conversation rehydrates from localStorage.
    firstRender.unmount();
    const secondRender = render(<App />);
    expect(
      screen.getByText("First question after reload?"),
    ).toBeInTheDocument();

    // Continue chatting after the reload — the appended turn must persist too.
    await ask("Second question after reload?");
    expect(
      screen.getByText("Second question after reload?"),
    ).toBeInTheDocument();

    // Second reload: BOTH turns survive, proving the post-reload turn was
    // written through to localStorage, not just held in memory.
    secondRender.unmount();
    render(<App />);
    expect(
      screen.getByText("First question after reload?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Second question after reload?"),
    ).toBeInTheDocument();
  });

  it("rehydrates the archived previous-chats list after a reload / new tab (AC-S1, UJ-025)", async () => {
    const firstRender = render(<App />);
    await ask("Please archive this conversation?");

    // Archive the active conversation, then start chatting in the fresh one.
    fireEvent.click(screen.getByRole("button", { name: /new chat/i }));
    await ask("This is the brand-new conversation?");

    // Reload (or open a new tab of the same origin): both the active
    // conversation AND the archived previous-chats list come back.
    firstRender.unmount();
    render(<App />);

    expect(
      screen.getByText("This is the brand-new conversation?"),
    ).toBeInTheDocument();

    const toggle = screen.getByRole("button", { name: /previous chats/i });
    fireEvent.click(toggle);
    expect(
      within(screen.getByTestId("previous-chats-list")).getByText(
        /please archive this conversation\?/i,
      ),
    ).toBeInTheDocument();
  });

  it("keeps chatting in-memory when localStorage is unavailable (TC-073, AC-S2)", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation((key: string) => {
      if (key === "vecinita.chat.history.v1") {
        throw new Error("storage disabled");
      }
      return null;
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation((key: string) => {
      if (key === "vecinita.chat.history.v1") {
        throw new Error("quota exceeded");
      }
    });

    const question = "Is the clinic open today?";
    render(<App />);

    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: question },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(await screen.findByText(question)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Local aid info\./)).toBeInTheDocument();
    });
  });
});
