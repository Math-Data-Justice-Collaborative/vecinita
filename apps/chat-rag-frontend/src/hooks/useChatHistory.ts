import { useCallback, useState } from "react";

import type { ChatMessage, Source } from "../api/types";

function newId(): string {
  return crypto.randomUUID();
}

/** Client-side-only conversation history (F3, ADR-004). Never sent to the server. */
export function useChatHistory() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // In-flight ask state lives here (not inside ChatPanel) so it is lifted into
  // the always-mounted shell alongside `messages`. This keeps Ask blocked while
  // a stream is still running across a Chat ⇄ Corpus round-trip, preventing a
  // concurrent stream (BUG-2026-06-25, PR #68).
  const [loading, setLoading] = useState(false);

  const appendUserMessage = useCallback((content: string) => {
    const message: ChatMessage = { id: newId(), role: "user", content };
    setMessages((prev) => [...prev, message]);
    return message.id;
  }, []);

  const appendAssistantPlaceholder = useCallback(() => {
    const message: ChatMessage = {
      id: newId(),
      role: "assistant",
      content: "",
    };
    setMessages((prev) => [...prev, message]);
    return message.id;
  }, []);

  const appendAssistantToken = useCallback(
    (messageId: string, token: string) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, content: msg.content + token } : msg,
        ),
      );
    },
    [],
  );

  const setAssistantSources = useCallback(
    (messageId: string, sources: Source[]) => {
      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, sources } : msg)),
      );
    },
    [],
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    appendUserMessage,
    appendAssistantPlaceholder,
    appendAssistantToken,
    setAssistantSources,
    clearHistory,
    loading,
    setLoading,
  };
}

/** Shape returned by {@link useChatHistory}; lifted to the app shell so it
 *  survives Chat ⇄ Corpus navigation (BUG-2026-06-25, issue #53). */
export type ChatHistory = ReturnType<typeof useChatHistory>;
