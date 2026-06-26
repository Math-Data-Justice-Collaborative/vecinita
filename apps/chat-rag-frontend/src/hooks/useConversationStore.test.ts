import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ChatMessage } from "../api/types";
import {
  CHAT_HISTORY_STORAGE_KEY,
  PREVIOUS_CHATS_CAP,
  useConversationStore,
} from "./useConversationStore";

function userMessage(content: string): ChatMessage {
  return { id: crypto.randomUUID(), role: "user", content };
}

describe("useConversationStore", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("rehydrates the active conversation with sources after a remount (TC-072)", () => {
    const first = renderHook(() => useConversationStore());
    act(() => {
      first.result.current.setActiveMessages(() => [
        { id: "u1", role: "user", content: "Where is the food pantry?" },
        {
          id: "a1",
          role: "assistant",
          content: "It is on Main St.",
          sources: [
            {
              chunk_id: "c1",
              document_id: "d1",
              title: "Pantry",
              url: "https://example.com",
              score: 0.9,
            },
          ],
        },
      ]);
    });
    first.unmount();

    const second = renderHook(() => useConversationStore());
    const { messages } = second.result.current.active;
    expect(messages).toHaveLength(2);
    expect(messages[0].content).toBe("Where is the food pantry?");
    expect(messages[1].sources?.[0].title).toBe("Pantry");
  });

  it("falls back to in-memory state when sessionStorage throws (TC-073)", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("storage disabled");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota exceeded");
    });

    const { result } = renderHook(() => useConversationStore());
    expect(() => {
      act(() => {
        result.current.setActiveMessages(() => [userMessage("still works")]);
      });
    }).not.toThrow();
    expect(result.current.active.messages).toHaveLength(1);
  });

  it("ignores corrupt or unsupported stored payloads", () => {
    sessionStorage.setItem(CHAT_HISTORY_STORAGE_KEY, "{ not json");
    const corrupt = renderHook(() => useConversationStore());
    expect(corrupt.result.current.active.messages).toHaveLength(0);
    corrupt.unmount();

    sessionStorage.setItem(
      CHAT_HISTORY_STORAGE_KEY,
      JSON.stringify({ version: 2, active: {}, previous: [] }),
    );
    const futureVersion = renderHook(() => useConversationStore());
    expect(futureVersion.result.current.active.messages).toHaveLength(0);
    expect(futureVersion.result.current.previous).toHaveLength(0);
  });

  it("caps the previous list at 10 conversations and evicts the oldest (TC-075)", () => {
    const { result } = renderHook(() => useConversationStore());
    for (let i = 0; i <= PREVIOUS_CHATS_CAP; i++) {
      act(() => {
        result.current.setActiveMessages(() => [
          userMessage(`conv ${String(i)}`),
        ]);
      });
      act(() => {
        result.current.newChat();
      });
    }

    const { previous } = result.current;
    expect(previous).toHaveLength(PREVIOUS_CHATS_CAP);
    expect(previous[0].messages[0].content).toBe("conv 10");
    expect(previous.some((conv) => conv.messages[0].content === "conv 0")).toBe(
      false,
    );
  });

  it("selects, deletes, clears all, and clears the active conversation (TC-076)", () => {
    const { result } = renderHook(() => useConversationStore());
    act(() => {
      result.current.setActiveMessages(() => [userMessage("first")]);
    });
    act(() => {
      result.current.newChat();
    });
    act(() => {
      result.current.setActiveMessages(() => [userMessage("second")]);
    });
    act(() => {
      result.current.newChat();
    });
    expect(result.current.previous).toHaveLength(2);

    const firstConv = result.current.previous.find(
      (conv) => conv.messages[0].content === "first",
    );
    act(() => {
      result.current.selectConversation(firstConv?.id ?? "");
    });
    expect(result.current.active.messages[0].content).toBe("first");
    expect(
      result.current.previous.some((conv) => conv.id === firstConv?.id),
    ).toBe(false);

    const secondConv = result.current.previous.find(
      (conv) => conv.messages[0].content === "second",
    );
    act(() => {
      result.current.deleteConversation(secondConv?.id ?? "");
    });
    expect(
      result.current.previous.some((conv) => conv.id === secondConv?.id),
    ).toBe(false);

    act(() => {
      result.current.clearActive();
    });
    expect(result.current.active.messages).toHaveLength(0);

    act(() => {
      result.current.setActiveMessages(() => [userMessage("third")]);
    });
    act(() => {
      result.current.newChat();
    });
    expect(result.current.previous.length).toBeGreaterThan(0);
    act(() => {
      result.current.clearAll();
    });
    expect(result.current.previous).toHaveLength(0);
  });

  it("archives a non-empty active conversation when selecting a previous one", () => {
    const { result } = renderHook(() => useConversationStore());
    act(() => {
      result.current.setActiveMessages(() => [userMessage("alpha")]);
    });
    act(() => {
      result.current.newChat();
    });
    const alphaId = result.current.previous[0].id;
    act(() => {
      result.current.setActiveMessages(() => [userMessage("beta")]);
    });
    act(() => {
      result.current.selectConversation(alphaId);
    });

    expect(result.current.active.messages[0].content).toBe("alpha");
    expect(
      result.current.previous.some(
        (conv) => conv.messages[0].content === "beta",
      ),
    ).toBe(true);
  });

  it("ignores newChat on an empty active conversation and unknown ids", () => {
    const { result } = renderHook(() => useConversationStore());
    act(() => {
      result.current.newChat();
    });
    expect(result.current.previous).toHaveLength(0);

    act(() => {
      result.current.selectConversation("does-not-exist");
    });
    act(() => {
      result.current.deleteConversation("does-not-exist");
    });
    expect(result.current.active.messages).toHaveLength(0);
    expect(result.current.previous).toHaveLength(0);
  });
});
