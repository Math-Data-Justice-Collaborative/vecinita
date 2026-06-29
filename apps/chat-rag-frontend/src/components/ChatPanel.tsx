import { type FormEvent, useEffect, useState } from "react";

import {
  formatAskFailureMessage,
  isDoneEvent,
  isSourcesEvent,
  isTokenEvent,
  streamAsk,
} from "../api/ask";
import { prewarmChatServices } from "../api/warm";
import type { Source } from "../api/types";
import { requireChatApiConfig } from "../config";
import { useLocale } from "../hooks/useLocale";
import { useChatHistory, type ChatHistory } from "../hooks/useChatHistory";
import { useConversationStore } from "../hooks/useConversationStore";
import { t } from "../i18n/messages";
import { SourceList } from "./SourceList";
import { SuggestedQuestions } from "./SuggestedQuestions";

type ChatPanelProps = {
  /** Conversation history (and in-flight ask state) lifted to the app shell so it
   *  survives Chat ⇄ Corpus navigation (BUG-2026-06-25, issue #53 + PR #68).
   *  When omitted, a local instance is used (standalone use / unit tests). */
  chat?: ChatHistory;
  /** Topic tags selected in the sidebar (lifted to the shell, D3). Sent with the
   *  ask request when non-empty. */
  selectedTags?: string[];
};

/**
 * Renders standalone with its own local chat history. Split out so the
 * `useChatHistory` hook is only called when no `chat` is injected — when the app
 * shell supplies one, `ChatPanelView` runs without an unused fallback hook
 * (PR #68 review), while still honoring the rules of hooks.
 */
function ChatPanelStandalone({ selectedTags }: { selectedTags: string[] }) {
  const store = useConversationStore();
  const chat = useChatHistory(store);
  return <ChatPanelView chat={chat} selectedTags={selectedTags} />;
}

export function ChatPanel({ chat, selectedTags = [] }: ChatPanelProps = {}) {
  if (chat) {
    return <ChatPanelView chat={chat} selectedTags={selectedTags} />;
  }
  return <ChatPanelStandalone selectedTags={selectedTags} />;
}

function ChatPanelView({
  chat,
  selectedTags,
}: {
  chat: ChatHistory;
  selectedTags: string[];
}) {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { locale } = useLocale();
  const {
    messages,
    appendUserMessage,
    appendAssistantPlaceholder,
    appendAssistantToken,
    setAssistantSources,
    clearHistory,
    loading,
    setLoading,
  } = chat;

  useEffect(() => {
    try {
      const { baseUrl } = requireChatApiConfig();
      prewarmChatServices(baseUrl);
    } catch {
      // Config missing in tests or misconfigured deploy; chat still works without pre-warm.
    }
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }

    setError(null);
    setStatusMessage(null);
    setLoading(true);
    appendUserMessage(trimmed);
    setQuestion("");
    const assistantId = appendAssistantPlaceholder();

    try {
      const { baseUrl } = requireChatApiConfig();
      let sources: Source[] = [];

      for await (const chunk of streamAsk(trimmed, baseUrl, {
        language: locale,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        onRetry: () => {
          setStatusMessage(t(locale, "coldStartStatus"));
        },
      })) {
        setStatusMessage(null);
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
      const message = formatAskFailureMessage(err, locale);
      setError(message);
      appendAssistantToken(assistantId, message);
    } finally {
      setStatusMessage(null);
      setLoading(false);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <section
      className="chat-panel"
      data-empty={isEmpty}
      aria-label={t(locale, "chatPanelLabel")}
    >
      <div className="message-list" data-testid="message-list">
        {isEmpty ? (
          <div className="welcome">
            <h2 className="welcome-heading">{t(locale, "welcomeHeading")}</h2>
            <p className="empty-hint">{t(locale, "emptyHint")}</p>
          </div>
        ) : (
          messages.map((msg) => (
            <article
              key={msg.id}
              className={`message message-${msg.role}`}
              data-testid="message"
            >
              <p className="message-role">
                {msg.role === "user"
                  ? t(locale, "roleUser")
                  : t(locale, "roleAssistant")}
              </p>
              <p className="message-content">
                {msg.content || (loading ? "…" : "")}
              </p>
              {msg.sources && msg.sources.length > 0 ? (
                <SourceList sources={msg.sources} locale={locale} />
              ) : null}
            </article>
          ))
        )}
      </div>

      {statusMessage ? (
        <p className="status-hint" role="status">
          {statusMessage}
        </p>
      ) : null}

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <form className="chat-form" onSubmit={(e) => void handleSubmit(e)}>
        {isEmpty ? (
          <SuggestedQuestions locale={locale} onSelect={setQuestion} />
        ) : null}
        <label className="sr-only" htmlFor="question">
          {t(locale, "yourQuestion")}
        </label>
        <div className="chat-input-row">
          <textarea
            id="question"
            name="question"
            rows={1}
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
            }}
            disabled={loading}
            placeholder={t(locale, "questionPlaceholder")}
          />
          <div className="form-actions">
            <button type="submit" disabled={loading || !question.trim()}>
              {loading ? t(locale, "asking") : t(locale, "ask")}
            </button>
            <button
              type="button"
              className="secondary"
              disabled={loading || isEmpty}
              onClick={clearHistory}
            >
              {t(locale, "clearHistory")}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
