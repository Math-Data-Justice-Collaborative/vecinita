import { FormEvent, useState } from "react";

import { isDoneEvent, isSourcesEvent, isTokenEvent, streamAsk } from "../api/ask";
import type { Source } from "../api/types";
import { requireChatApiConfig } from "../config";
import { useChatHistory } from "../hooks/useChatHistory";
import { SourceList } from "./SourceList";

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const {
    messages,
    appendUserMessage,
    appendAssistantPlaceholder,
    appendAssistantToken,
    setAssistantSources,
    clearHistory,
  } = useChatHistory();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }

    setError(null);
    setLoading(true);
    appendUserMessage(trimmed);
    setQuestion("");
    const assistantId = appendAssistantPlaceholder();

    try {
      const { baseUrl } = requireChatApiConfig();
      let sources: Source[] = [];

      for await (const chunk of streamAsk(trimmed, baseUrl)) {
        if (isTokenEvent(chunk)) {
          appendAssistantToken(assistantId, chunk.token);
        } else if (isSourcesEvent(chunk)) {
          sources = chunk.sources;
        } else if (isDoneEvent(chunk)) {
          break;
        }
      }

      setAssistantSources(assistantId, sources);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed";
      setError(message);
      appendAssistantToken(assistantId, message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat-panel" aria-label="Community Q&A chat">
      <div className="message-list" data-testid="message-list">
        {messages.length === 0 ? (
          <p className="empty-hint">Ask a question in English or Spanish about your community.</p>
        ) : (
          messages.map((msg) => (
            <article key={msg.id} className={`message message-${msg.role}`} data-testid="message">
              <p className="message-role">{msg.role === "user" ? "You" : "Vecinita"}</p>
              <p className="message-content">{msg.content || (loading ? "…" : "")}</p>
              {msg.sources && msg.sources.length > 0 ? <SourceList sources={msg.sources} /> : null}
            </article>
          ))
        )}
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <form className="chat-form" onSubmit={(e) => void handleSubmit(e)}>
        <label htmlFor="question">Your question</label>
        <textarea
          id="question"
          name="question"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
          placeholder="e.g. When is the food pantry open?"
        />
        <div className="form-actions">
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking…" : "Ask"}
          </button>
          <button
            type="button"
            className="secondary"
            disabled={loading || messages.length === 0}
            onClick={clearHistory}
          >
            Clear history
          </button>
        </div>
      </form>
    </section>
  );
}
