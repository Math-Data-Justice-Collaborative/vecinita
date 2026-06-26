import { useCallback, useEffect, useRef, useState } from "react";

import type { ChatMessage, Source } from "../api/types";

/** Device-only, tab-scoped storage key (ADR-023/024, F33). */
export const CHAT_HISTORY_STORAGE_KEY = "vecinita.chat.history.v1";
/** Keep at most the last N conversations in the previous-chats list (RD-070). */
export const PREVIOUS_CHATS_CAP = 10;

export type Conversation = {
  id: string;
  messages: ChatMessage[];
  createdAt: number;
};

/** Serialized envelope persisted to `sessionStorage` (ADR-024). */
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

function isSource(value: unknown): value is Source {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.chunk_id === "string" &&
    typeof candidate.document_id === "string" &&
    typeof candidate.score === "number"
  );
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  if (
    typeof candidate.id !== "string" ||
    typeof candidate.content !== "string" ||
    (candidate.role !== "user" && candidate.role !== "assistant")
  ) {
    return false;
  }
  if (candidate.sources !== undefined) {
    return (
      Array.isArray(candidate.sources) && candidate.sources.every(isSource)
    );
  }
  return true;
}

function isConversation(value: unknown): value is Conversation {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.createdAt === "number" &&
    Array.isArray(candidate.messages) &&
    candidate.messages.every(isChatMessage)
  );
}

function isEnvelope(value: unknown): value is ChatHistoryEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    candidate.version === 1 &&
    isConversation(candidate.active) &&
    Array.isArray(candidate.previous) &&
    candidate.previous.every(isConversation)
  );
}

/** Read + validate the persisted envelope. Returns null on absence/corruption/failure. */
function readEnvelope(): ChatHistoryEnvelope | null {
  try {
    const raw = sessionStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
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
  clearActive: () => void;
  newChat: () => void;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  clearAll: () => void;
};

/**
 * Owns the active conversation plus a capped previous-conversations list,
 * write-through to device-only, tab-scoped `sessionStorage` (ADR-023/024, F33).
 * Lifted to the app shell so it survives refresh / tab-away. Degrades silently
 * to in-memory state if `sessionStorage` is unavailable (TC-073, AC-S2).
 */
export function useConversationStore(): ConversationStore {
  const [envelope, setEnvelope] = useState<ChatHistoryEnvelope>(
    () => readEnvelope() ?? emptyEnvelope(),
  );

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
      sessionStorage.setItem(
        CHAT_HISTORY_STORAGE_KEY,
        JSON.stringify(envelope),
      );
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
        previous: [current.active, ...current.previous].slice(
          0,
          PREVIOUS_CHATS_CAP,
        ),
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
          ? [current.active, ...remaining].slice(0, PREVIOUS_CHATS_CAP)
          : remaining;
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
    clearActive,
    newChat,
    selectConversation,
    deleteConversation,
    clearAll,
  };
}
