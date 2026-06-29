import type { TagFacet } from "../api/browse";
import type { Conversation } from "../hooks/useConversationStore";
import type { Locale } from "../hooks/useLocale.types";
import type { Theme } from "../hooks/useTheme";
import { t } from "../i18n/messages";
import { LanguageToggle } from "./LanguageToggle";
import { PreviousChatsList } from "./PreviousChatsList";
import { TagFilterChips } from "./TagFilterChips";
import { ThemeToggle } from "./ThemeToggle";

type SidebarProps = {
  open: boolean;
  locale: Locale;
  theme: Theme;
  onCorpus: boolean;
  newChatDisabled: boolean;
  tags: TagFacet[];
  selectedTags: string[];
  previousChats: Conversation[];
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
  newChatDisabled,
  tags,
  selectedTags,
  previousChats,
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

      <button
        type="button"
        className="sidebar-new-chat"
        disabled={newChatDisabled}
        onClick={onNewChat}
      >
        <span aria-hidden="true">+ </span>
        {t(locale, "newChat")}
      </button>

      <nav className="sidebar-nav" aria-label="Primary">
        <button
          type="button"
          className={onCorpus ? "sidebar-nav-item" : "sidebar-nav-item active"}
          aria-current={onCorpus ? undefined : "page"}
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
