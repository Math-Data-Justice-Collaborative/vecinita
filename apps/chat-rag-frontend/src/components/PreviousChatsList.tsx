import { useState } from "react";

import type { Conversation } from "../hooks/useConversationStore";
import type { Locale } from "../hooks/useLocale.types";
import { t } from "vecinita-frontend-i18n";
import { formatRelativeTime } from "../i18n/relativeTime";
import { deriveConversationLabel } from "./previousChatsLabel";

type PreviousChatsListProps = {
  conversations: Conversation[];
  locale: Locale;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClearAll: () => void;
  /** When true, selecting a previous chat is blocked (e.g. stream in flight). */
  selectDisabled?: boolean;
};

/**
 * Collapsible list of previous conversations on the main Chat page (F33,
 * UJ-025). Select restores a conversation; per-item delete and "Clear all
 * history" manage the device-local `localStorage`-backed list.
 */
export function PreviousChatsList({
  conversations,
  locale,
  onSelect,
  onDelete,
  onClearAll,
  selectDisabled = false,
}: PreviousChatsListProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section
      className="previous-chats"
      aria-label={t(locale, "chat.previousChats")}
      data-testid="previous-chats"
    >
      <button
        type="button"
        className="previous-chats-toggle"
        aria-expanded={expanded}
        onClick={() => {
          setExpanded((value) => !value);
        }}
      >
        {`${t(locale, "chat.previousChats")} (${String(conversations.length)})`}
      </button>

      {expanded ? (
        conversations.length === 0 ? (
          <p className="empty-hint">{t(locale, "chat.noPreviousChats")}</p>
        ) : (
          <>
            <ul
              className="previous-chats-list"
              data-testid="previous-chats-list"
            >
              {conversations.map((conversation) => (
                <li key={conversation.id} className="previous-chats-item">
                  <button
                    type="button"
                    className="previous-chat-select"
                    disabled={selectDisabled}
                    onClick={() => {
                      onSelect(conversation.id);
                    }}
                  >
                    <span className="previous-chat-label">
                      {deriveConversationLabel(conversation)}
                    </span>
                    <span className="previous-chat-time">
                      {formatRelativeTime(conversation.createdAt, locale)}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="previous-chat-delete"
                    aria-label={t(locale, "chat.deleteConversation")}
                    onClick={() => {
                      onDelete(conversation.id);
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="secondary previous-chats-clear-all"
              onClick={onClearAll}
            >
              {t(locale, "chat.clearAllHistory")}
            </button>
          </>
        )
      ) : null}
    </section>
  );
}
