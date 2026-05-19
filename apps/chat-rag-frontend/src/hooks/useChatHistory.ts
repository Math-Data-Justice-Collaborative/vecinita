import { useCallback, useState } from "react";

import type { ChatMessage, Source } from "../api/types";

function newId(): string {
  return crypto.randomUUID();
}

/** Client-side-only conversation history (F3, ADR-004). Never sent to the server. */
export function useChatHistory() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const appendUserMessage = useCallback((content: string) => {
    const message: ChatMessage = { id: newId(), role: "user", content };
    setMessages((prev) => [...prev, message]);
    return message.id;
  }, []);

  const appendAssistantPlaceholder = useCallback(() => {
    const message: ChatMessage = { id: newId(), role: "assistant", content: "" };
    setMessages((prev) => [...prev, message]);
    return message.id;
  }, []);

  const appendAssistantToken = useCallback((messageId: string, token: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, content: msg.content + token } : msg,
      ),
    );
  }, []);

  const setAssistantSources = useCallback((messageId: string, sources: Source[]) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, sources } : msg)),
    );
  }, []);

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
  };
}
