import { FormEvent, useEffect, useState } from "react";

import {
  formatAskFailureMessage,
  isDoneEvent,
  isSourcesEvent,
  isTokenEvent,
  streamAsk,
} from "../api/ask";
import { fetchTags, type TagFacet } from "../api/browse";
import { prewarmChatServices } from "../api/warm";
import type { Source } from "../api/types";
import { requireChatApiConfig } from "../config";
import { useLocale } from "../hooks/useLocale";
import { useChatHistory, type ChatHistory } from "../hooks/useChatHistory";
import { useConversationStore } from "../hooks/useConversationStore";
import { t } from "../i18n/messages";
import { TagFilterChips } from "./TagFilterChips";
import { SourceList } from "./SourceList";

type ChatPanelProps = {
  /** Conversation history (and in-flight ask state) lifted to the app shell so it
   *  survives Chat ⇄ Corpus navigation (BUG-2026-06-25, issue #53 + PR #68).
   *  When omitted, a local instance is used (standalone use / unit tests). */
  chat?: ChatHistory;
};

/**
 * Renders standalone with its own local chat history. Split out so the
 * `useChatHistory` hook is only called when no `chat` is injected — when the app
 * shell supplies one, `ChatPanelView` runs without an unused fallback hook
 * (PR #68 review), while still honoring the rules of hooks.
 */
function ChatPanelStandalone() {
  const store = useConversationStore();
  const chat = useChatHistory(store);
  return <ChatPanelView chat={chat} />;
}

export function ChatPanel({ chat }: ChatPanelProps = {}) {
  if (chat) {
    return <ChatPanelView chat={chat} />;
  }
  return <ChatPanelStandalone />;
}

function ChatPanelView({ chat }: { chat: ChatHistory }) {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [tagFacets, setTagFacets] = useState<TagFacet[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
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

  useEffect(() => {
    let cancelled = false;
    async function loadTags() {
      try {
        const response = await fetchTags();
        if (!cancelled) {
          setTagFacets(response.tags);
        }
      } catch {
        // Tag chips are optional; chat still works without facets.
      }
    }
    void loadTags();
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleTag(slug: string) {
    setSelectedTags((current) =>
      current.includes(slug)
        ? current.filter((item) => item !== slug)
        : [...current, slug],
    );
  }

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

  return (
    <section className="chat-panel" aria-label={t(locale, "chatPanelLabel")}>
      {tagFacets.length > 0 ? (
        <TagFilterChips
          tags={tagFacets}
          selected={selectedTags}
          locale={locale}
          onToggle={toggleTag}
        />
      ) : null}
      <div className="message-list" data-testid="message-list">
        {messages.length === 0 ? (
          <p className="empty-hint">{t(locale, "emptyHint")}</p>
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
        <label htmlFor="question">{t(locale, "yourQuestion")}</label>
        <textarea
          id="question"
          name="question"
          rows={3}
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
            disabled={loading || messages.length === 0}
            onClick={clearHistory}
          >
            {t(locale, "clearHistory")}
          </button>
        </div>
      </form>
    </section>
  );
}
