import { FormEvent, useEffect, useState } from "react";

import {
  formatAskFailureMessage,
  isDoneEvent,
  isSourcesEvent,
  isTokenEvent,
  streamAsk,
} from "../api/ask";
import { fetchTags, type TagFacet } from "../api/browse";
import type { Source } from "../api/types";
import { requireChatApiConfig } from "../config";
import { useLocale } from "../hooks/useLocale";
import { useChatHistory } from "../hooks/useChatHistory";
import { t } from "../i18n/messages";
import { TagFilterChips } from "./TagFilterChips";
import { SourceList } from "./SourceList";

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
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
  } = useChatHistory();

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
