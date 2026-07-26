import { useCallback, useState } from "react";

import type { ChatMessage, Source } from "../api/types";
import type { ConversationStore } from "./useConversationStore";

function newId(): string {
  return crypto.randomUUID();
}

/**
 * Client-side-only conversation history (F3, ADR-004). Never sent to the
 * server. Backs onto a {@link ConversationStore} so the active conversation is
 * write-through to device-local `localStorage` and survives refresh / tab-away,
 * a tab close, and new tabs (F33, ADR-023/024/025). The store is supplied by the
 * always-mounted shell (or a standalone instance for tests / standalone use),
 * preserving the Chat ⇄ Corpus navigation guard (BUG-2026-06-25, issue #53).
 */
export function useChatHistory(store: ConversationStore) {
  // In-flight ask state lives here (not inside ChatPanel) so it is lifted into
  // the always-mounted shell alongside the conversation. This keeps Ask blocked
  // while a stream is still running across a Chat ⇄ Corpus round-trip,
  // preventing a concurrent stream (BUG-2026-06-25, PR #68).
  const [loading, setLoading] = useState(false);
  const { setActiveMessages, updateMessageById } = store;
  const messages = store.active.messages;

  const appendUserMessage = useCallback(
    (content: string) => {
      const message: ChatMessage = { id: newId(), role: "user", content };
      setActiveMessages((prev) => [...prev, message]);
      return message.id;
    },
    [setActiveMessages],
  );

  const appendAssistantPlaceholder = useCallback(() => {
    const message: ChatMessage = {
      id: newId(),
      role: "assistant",
      content: "",
    };
    setActiveMessages((prev) => [...prev, message]);
    return message.id;
  }, [setActiveMessages]);

  const appendAssistantToken = useCallback(
    (messageId: string, token: string) => {
      // Update by id across active + previous so mid-stream chat switches
      // (BUG-2026-07-25 / #145) do not drop tokens onto a blank archive.
      updateMessageById(messageId, (msg) => ({
        ...msg,
        content: msg.content + token,
      }));
    },
    [updateMessageById],
  );

  const setAssistantSources = useCallback(
    (messageId: string, sources: Source[]) => {
      updateMessageById(messageId, (msg) => ({ ...msg, sources }));
    },
    [updateMessageById],
  );

  return {
    messages,
    appendUserMessage,
    appendAssistantPlaceholder,
    appendAssistantToken,
    setAssistantSources,
    clearHistory: store.clearActive,
    loading,
    setLoading,
    previousChats: store.previous,
    newChat: store.newChat,
    selectConversation: store.selectConversation,
    deleteConversation: store.deleteConversation,
    clearAll: store.clearAll,
  };
}

/** Shape returned by {@link useChatHistory}; lifted to the app shell so it
 *  survives Chat ⇄ Corpus navigation (#53) and refresh / tab-away (F33). */
export type ChatHistory = ReturnType<typeof useChatHistory>;
