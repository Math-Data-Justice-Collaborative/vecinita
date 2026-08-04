import type { TagFacet } from "../api/browse";
import type { Conversation } from "../hooks/useConversationStore";
import type { Locale } from "../hooks/useLocale.types";
import type { Theme } from "../hooks/useTheme";
import { t } from "../i18n/messages";
import { LanguageToggle } from "./LanguageToggle";
import { PreviousChatsList } from "./PreviousChatsList";
import { TagFilterChips } from "./TagFilterChips";
import { ThemeToggle } from "./ThemeToggle";
import { ActionIcon, Tooltip } from "vecinita-frontend-ui";
import { t as i18nT } from "vecinita-frontend-i18n";

type SidebarProps = {
  open: boolean;
  locale: Locale;
  theme: Theme;
  onCorpus: boolean;
  onFeedback: boolean;
  newChatDisabled: boolean;
  tags: TagFacet[];
  selectedTags: string[];
  previousChats: Conversation[];
  /** Block selecting previous chats while an ask stream is in flight (#145). */
  previousSelectDisabled?: boolean;
  onNavigate: (path: string) => void;
  onNewChat: () => void;
  onToggleTag: (slug: string) => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onClearAll: () => void;
  onSetLocale: (locale: Locale) => void;
  onToggleTheme: () => void;
};

/**
 * Persistent left sidebar (ChatGPT-style redesign, D3). Hosts new-chat,
 * Chat/Corpus navigation, topic (tag) filters, the recent-chats list, and the
 * language + theme controls. Collapses off-canvas on narrow screens (D7).
 */
export function Sidebar({
  open,
  locale,
  theme,
  onCorpus,
  onFeedback,
  newChatDisabled,
  tags,
  selectedTags,
  previousChats,
  previousSelectDisabled = false,
  onNavigate,
  onNewChat,
  onToggleTag,
  onSelectConversation,
  onDeleteConversation,
  onClearAll,
  onSetLocale,
  onToggleTheme,
}: SidebarProps) {
  return (
    <aside
      className="sidebar"
      data-testid="sidebar"
      data-open={open}
      aria-label={t(locale, "menuLabel")}
    >
      <div className="sidebar-brand">{t(locale, "appTitle")}</div>

      <Tooltip content={i18nT(locale, "chat.tooltip.newChat")}>
        <button
          type="button"
          className="sidebar-new-chat"
          disabled={newChatDisabled}
          onClick={onNewChat}
          data-testid="sidebar-new-chat"
        >
          <ActionIcon motion="press" pending={false} aria-hidden="true">
            <span>+ </span>
          </ActionIcon>
          {t(locale, "newChat")}
        </button>
      </Tooltip>

      <nav className="sidebar-nav" aria-label="Primary">
        <button
          type="button"
          className={
            onCorpus || onFeedback
              ? "sidebar-nav-item"
              : "sidebar-nav-item active"
          }
          aria-current={onCorpus || onFeedback ? undefined : "page"}
          onClick={() => {
            onNavigate("/");
          }}
        >
          {t(locale, "navChat")}
        </button>
        <button
          type="button"
          className={onCorpus ? "sidebar-nav-item active" : "sidebar-nav-item"}
          aria-current={onCorpus ? "page" : undefined}
          onClick={() => {
            onNavigate("/corpus");
          }}
        >
          {t(locale, "navCorpus")}
        </button>
        <button
          type="button"
          className={
            onFeedback ? "sidebar-nav-item active" : "sidebar-nav-item"
          }
          aria-current={onFeedback ? "page" : undefined}
          data-testid="nav-feedback"
          onClick={() => {
            onNavigate("/feedback");
          }}
        >
          {t(locale, "navFeedback")}
        </button>
      </nav>

      {tags.length > 0 ? (
        <section className="sidebar-section">
          <h2 className="sidebar-heading">{t(locale, "topicsHeading")}</h2>
          <TagFilterChips
            tags={tags}
            selected={selectedTags}
            locale={locale}
            onToggle={onToggleTag}
          />
        </section>
      ) : null}

      <section className="sidebar-section sidebar-recent">
        <PreviousChatsList
          conversations={previousChats}
          locale={locale}
          selectDisabled={previousSelectDisabled}
          onSelect={onSelectConversation}
          onDelete={onDeleteConversation}
          onClearAll={onClearAll}
        />
      </section>

      <div className="sidebar-footer">
        <LanguageToggle locale={locale} onChange={onSetLocale} />
        <ThemeToggle theme={theme} locale={locale} onToggle={onToggleTheme} />
      </div>
    </aside>
  );
}
