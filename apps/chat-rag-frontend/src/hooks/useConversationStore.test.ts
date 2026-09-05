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
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
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
    expect(messages[0]?.content).toBe("Where is the food pantry?");
    expect(messages[1]?.sources?.[0]?.title).toBe("Pantry");
  });

  it("persists across separate store instances sharing localStorage (new tab / reopen, ADR-025)", () => {
    const first = renderHook(() => useConversationStore());
    act(() => {
      first.result.current.setActiveMessages(() => [
        userMessage("survives tab close"),
      ]);
    });
    // A brand-new tab (or reopened browser) constructs a fresh store instance
    // but reads the same device-local `localStorage`.
    first.unmount();

    const reopened = renderHook(() => useConversationStore());
    expect(reopened.result.current.active.messages[0]?.content).toBe(
      "survives tab close",
    );
  });

  it("falls back to in-memory state when localStorage throws (TC-073)", () => {
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

  it("rehydrates assistant energyEstimate when valid (F65)", () => {
    const first = renderHook(() => useConversationStore());
    act(() => {
      first.result.current.setActiveMessages(() => [
        { id: "u1", role: "user", content: "hours?" },
        {
          id: "a1",
          role: "assistant",
          content: "Open daily.",
          energyEstimate: {
            wh: 0.02,
            g_co2e: 0.008,
            method: "tdp_util_walltime_v1",
            advisory: "Approximate.",
            car_km_equiv: 0.00003,
            car_m_equiv: 0.03,
          },
        },
      ]);
    });
    first.unmount();

    const second = renderHook(() => useConversationStore());
    expect(second.result.current.active.messages[1]?.energyEstimate?.wh).toBe(
      0.02,
    );
  });

  it("ignores messages with invalid energyEstimate shapes (F65)", () => {
    localStorage.setItem(
      CHAT_HISTORY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        active: {
          id: "a",
          createdAt: 1,
          messages: [
            {
              id: "a1",
              role: "assistant",
              content: "x",
              energyEstimate: { wh: 1, method: "wrong" },
            },
          ],
        },
        previous: [],
      }),
    );
    const { result } = renderHook(() => useConversationStore());
    expect(result.current.active.messages).toHaveLength(0);
  });

  it("ignores corrupt or unsupported stored payloads", () => {
    localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, "{ not json");
    const corrupt = renderHook(() => useConversationStore());
    expect(corrupt.result.current.active.messages).toHaveLength(0);
    corrupt.unmount();

    localStorage.setItem(
      CHAT_HISTORY_STORAGE_KEY,
      JSON.stringify({ version: 2, active: {}, previous: [] }),
    );
    const futureVersion = renderHook(() => useConversationStore());
    expect(futureVersion.result.current.active.messages).toHaveLength(0);
    expect(futureVersion.result.current.previous).toHaveLength(0);
  });

  it.each([
    ["a non-object envelope", JSON.stringify("hello")],
    [
      "active is not a conversation",
      JSON.stringify({ version: 1, active: "x", previous: [] }),
    ],
    [
      "an active message is not an object",
      JSON.stringify({
        version: 1,
        active: { id: "a", createdAt: 0, messages: ["nope"] },
        previous: [],
      }),
    ],
    [
      "an active message has an invalid role",
      JSON.stringify({
        version: 1,
        active: {
          id: "a",
          createdAt: 0,
          messages: [{ id: "m", role: "bot", content: "x" }],
        },
        previous: [],
      }),
    ],
    [
      "a message source is not an object",
      JSON.stringify({
        version: 1,
        active: {
          id: "a",
          createdAt: 0,
          messages: [{ id: "m", role: "user", content: "x", sources: ["bad"] }],
        },
        previous: [],
      }),
    ],
    [
      "previous contains a non-conversation",
      JSON.stringify({
        version: 1,
        active: { id: "a", createdAt: 0, messages: [] },
        previous: ["x"],
      }),
    ],
  ])("ignores an invalid stored payload (%s)", (_label, payload) => {
    localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, payload);
    const { result } = renderHook(() => useConversationStore());
    expect(result.current.active.messages).toHaveLength(0);
    expect(result.current.previous).toHaveLength(0);
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
    expect(previous[0]?.messages[0]?.content).toBe("conv 10");
    expect(
      previous.some((conv) => conv.messages[0]?.content === "conv 0"),
    ).toBe(false);
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
      (conv) => conv.messages[0]?.content === "first",
    );
    act(() => {
      result.current.selectConversation(firstConv?.id ?? "");
    });
    expect(result.current.active.messages[0]?.content).toBe("first");
    expect(
      result.current.previous.some((conv) => conv.id === firstConv?.id),
    ).toBe(false);

    const secondConv = result.current.previous.find(
      (conv) => conv.messages[0]?.content === "second",
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

  it("keeps previous chats sorted by createdAt desc across select (#273)", () => {
    const older = {
      id: "c-old",
      createdAt: 1_700_000_000_001,
      messages: [userMessage("old")],
    };
    const mid = {
      id: "c-mid",
      createdAt: 1_700_000_000_002,
      messages: [userMessage("mid")],
    };
    const newer = {
      id: "c-new",
      createdAt: 1_700_000_000_003,
      messages: [userMessage("new")],
    };
    localStorage.setItem(
      CHAT_HISTORY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        active: {
          id: "c-active",
          createdAt: 1_700_000_000_004,
          messages: [userMessage("active")],
        },
        // Deliberately scrambled vs createdAt order
        previous: [mid, newer, older],
      }),
    );

    const { result } = renderHook(() => useConversationStore());
    expect(result.current.previous.map((c) => c.id)).toEqual([
      "c-new",
      "c-mid",
      "c-old",
    ]);

    act(() => {
      result.current.selectConversation("c-mid");
    });
    // Active (newest createdAt) archives into previous; list stays createdAt desc.
    expect(result.current.active.id).toBe("c-mid");
    expect(result.current.previous.map((c) => c.id)).toEqual([
      "c-active",
      "c-new",
      "c-old",
    ]);
    const createdAts = result.current.previous.map((c) => c.createdAt);
    expect(createdAts).toEqual([...createdAts].sort((a, b) => b - a));
  });

  it("archives a non-empty active conversation when selecting a previous one", () => {
    const { result } = renderHook(() => useConversationStore());
    act(() => {
      result.current.setActiveMessages(() => [userMessage("alpha")]);
    });
    act(() => {
      result.current.newChat();
    });
    const alphaId = result.current.previous[0]?.id ?? "";
    act(() => {
      result.current.setActiveMessages(() => [userMessage("beta")]);
    });
    act(() => {
      result.current.selectConversation(alphaId);
    });

    expect(result.current.active.messages[0]?.content).toBe("alpha");
    expect(
      result.current.previous.some(
        (conv) => conv.messages[0]?.content === "beta",
      ),
    ).toBe(true);
  });

  it("updateMessageById patches messages in previous after a mid-stream archive", () => {
    const { result } = renderHook(() => useConversationStore());
    const assistantId = "asst-inflight";
    act(() => {
      result.current.setActiveMessages(() => [
        userMessage("in flight"),
        { id: assistantId, role: "assistant", content: "" },
      ]);
    });
    act(() => {
      result.current.newChat();
    });
    act(() => {
      result.current.updateMessageById(assistantId, (msg) => ({
        ...msg,
        content: msg.content + "Recovered",
      }));
    });

    const archived = result.current.previous.find((conv) =>
      conv.messages.some((m) => m.id === assistantId),
    );
    expect(archived?.messages.find((m) => m.id === assistantId)?.content).toBe(
      "Recovered",
    );
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
