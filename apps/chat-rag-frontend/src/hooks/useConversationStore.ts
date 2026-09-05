import { useCallback, useEffect, useRef, useState } from "react";

import type { ChatMessage, Source } from "../api/types";

/** Device-local storage key (ADR-023/024/025, F33). Persisted to `localStorage`
 *  so history survives a tab close and is shared across tabs of the same
 *  origin; still device-only and never transmitted off the device. */
export const CHAT_HISTORY_STORAGE_KEY = "vecinita.chat.history.v1";
/** Keep at most the last N conversations in the previous-chats list (RD-070). */
export const PREVIOUS_CHATS_CAP = 10;

export type Conversation = {
  id: string;
  messages: ChatMessage[];
  createdAt: number;
};

/** Serialized envelope persisted to `localStorage` (ADR-024/025). */
type ChatHistoryEnvelope = {
  version: 1;
  active: Conversation;
  previous: Conversation[];
};

function newId(): string {
  return crypto.randomUUID();
}

function emptyConversation(): Conversation {
  return { id: newId(), messages: [], createdAt: Date.now() };
}

function emptyEnvelope(): ChatHistoryEnvelope {
  return { version: 1, active: emptyConversation(), previous: [] };
}

/** Newest-started first; stable across select/archive (#273 / ADR-024). */
function sortPreviousByCreatedAtDesc(
  conversations: Conversation[],
): Conversation[] {
  return [...conversations].sort((a, b) => b.createdAt - a.createdAt);
}

function cappedPrevious(conversations: Conversation[]): Conversation[] {
  return sortPreviousByCreatedAtDesc(conversations).slice(
    0,
    PREVIOUS_CHATS_CAP,
  );
}

function isSource(value: unknown): value is Source {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate["chunk_id"] === "string" &&
    typeof candidate["document_id"] === "string" &&
    typeof candidate["score"] === "number"
  );
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  if (
    typeof candidate["id"] !== "string" ||
    typeof candidate["content"] !== "string" ||
    (candidate["role"] !== "user" && candidate["role"] !== "assistant")
  ) {
    return false;
  }
  const sources = candidate["sources"];
  if (sources !== undefined) {
    if (!Array.isArray(sources) || !sources.every(isSource)) {
      return false;
    }
  }
  const energy = candidate["energyEstimate"];
  if (energy !== undefined) {
    if (typeof energy !== "object" || energy === null) {
      return false;
    }
    const e = energy as Record<string, unknown>;
    if (
      typeof e["wh"] !== "number" ||
      typeof e["g_co2e"] !== "number" ||
      typeof e["car_km_equiv"] !== "number" ||
      typeof e["car_m_equiv"] !== "number" ||
      typeof e["advisory"] !== "string" ||
      e["method"] !== "tdp_util_walltime_v1"
    ) {
      return false;
    }
  }
  return true;
}

function isConversation(value: unknown): value is Conversation {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate["id"] === "string" &&
    typeof candidate["createdAt"] === "number" &&
    Array.isArray(candidate["messages"]) &&
    candidate["messages"].every(isChatMessage)
  );
}

function isEnvelope(value: unknown): value is ChatHistoryEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    candidate["version"] === 1 &&
    isConversation(candidate["active"]) &&
    Array.isArray(candidate["previous"]) &&
    candidate["previous"].every(isConversation)
  );
}

/** Read + validate the persisted envelope. Returns null on absence/corruption/failure. */
function readEnvelope(): ChatHistoryEnvelope | null {
  try {
    const raw = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed: unknown = JSON.parse(raw);
    return isEnvelope(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/** Operations exposed by {@link useConversationStore}. */
export type ConversationStore = {
  active: Conversation;
  previous: Conversation[];
  setActiveMessages: (
    updater: (previous: ChatMessage[]) => ChatMessage[],
  ) => void;
  /** Patch a message by id in active or previous (survives mid-stream chat switch). */
  updateMessageById: (
    messageId: string,
    updater: (message: ChatMessage) => ChatMessage,
  ) => void;
  clearActive: () => void;
  newChat: () => void;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  clearAll: () => void;
};

/**
 * Owns the active conversation plus a capped previous-conversations list,
 * write-through to device-local `localStorage` (ADR-023/024/025, F33). Lifted to
 * the app shell so it survives refresh / tab-away; because it is `localStorage`
 * it also persists across a tab close and is shared with new tabs of the same
 * origin. Degrades silently to in-memory state if `localStorage` is unavailable
 * (TC-073, AC-S2).
 */
export function useConversationStore(): ConversationStore {
  const [envelope, setEnvelope] = useState<ChatHistoryEnvelope>(() => {
    const loaded = readEnvelope();
    if (!loaded) {
      return emptyEnvelope();
    }
    return {
      ...loaded,
      previous: cappedPrevious(loaded.previous),
    };
  });

  // Skip the redundant write on initial mount: the persisted state we just read
  // is already in storage, and a missing/corrupt payload need not be rewritten
  // until the user actually changes something.
  const hydrated = useRef(false);
  useEffect(() => {
    if (!hydrated.current) {
      hydrated.current = true;
      return;
    }
    try {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(envelope));
    } catch {
      // Quota exceeded / storage disabled: persistence is silently disabled
      // for this session; chat keeps working in-memory (TC-073, AC-S2).
    }
  }, [envelope]);

  const setActiveMessages = useCallback(
    (updater: (previous: ChatMessage[]) => ChatMessage[]) => {
      setEnvelope((current) => ({
        ...current,
        active: {
          ...current.active,
          messages: updater(current.active.messages),
        },
      }));
    },
    [],
  );

  const updateMessageById = useCallback(
    (messageId: string, updater: (message: ChatMessage) => ChatMessage) => {
      setEnvelope((current) => {
        const patch = (messages: ChatMessage[]): ChatMessage[] =>
          messages.map((msg) => (msg.id === messageId ? updater(msg) : msg));

        if (current.active.messages.some((msg) => msg.id === messageId)) {
          return {
            ...current,
            active: {
              ...current.active,
              messages: patch(current.active.messages),
            },
          };
        }

        const previous = current.previous.map((conv) => {
          if (!conv.messages.some((msg) => msg.id === messageId)) {
            return conv;
          }
          return { ...conv, messages: patch(conv.messages) };
        });
        const unchanged = previous.every(
          (conv, index) => conv === current.previous[index],
        );
        return unchanged ? current : { ...current, previous };
      });
    },
    [],
  );

  const clearActive = useCallback(() => {
    setEnvelope((current) => ({
      ...current,
      active: { ...current.active, messages: [] },
    }));
  }, []);

  const newChat = useCallback(() => {
    setEnvelope((current) => {
      if (current.active.messages.length === 0) {
        return current;
      }
      return {
        ...current,
        active: emptyConversation(),
        previous: cappedPrevious([current.active, ...current.previous]),
      };
    });
  }, []);

  const selectConversation = useCallback((id: string) => {
    setEnvelope((current) => {
      const target = current.previous.find((conv) => conv.id === id);
      if (!target) {
        return current;
      }
      const remaining = current.previous.filter((conv) => conv.id !== id);
      const previous =
        current.active.messages.length > 0
          ? cappedPrevious([current.active, ...remaining])
          : cappedPrevious(remaining);
      return { ...current, active: target, previous };
    });
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setEnvelope((current) => ({
      ...current,
      previous: current.previous.filter((conv) => conv.id !== id),
    }));
  }, []);

  const clearAll = useCallback(() => {
    setEnvelope((current) => ({ ...current, previous: [] }));
  }, []);

  return {
    active: envelope.active,
    previous: envelope.previous,
    setActiveMessages,
    updateMessageById,
    clearActive,
    newChat,
    selectConversation,
    deleteConversation,
    clearAll,
  };
}
