import { useState } from "react";

import { ChatPanel } from "./components/ChatPanel";
import { CorpusBrowse } from "./components/CorpusBrowse";
import { Sidebar } from "./components/Sidebar";
import { LocaleProvider } from "./context/LocaleContext";
import { useChatHistory } from "./hooks/useChatHistory";
import { useConversationStore } from "./hooks/useConversationStore";
import { useLocale } from "./hooks/useLocale";
import { usePathname } from "./hooks/usePathname";
import { useTagFilters } from "./hooks/useTagFilters";
import { useTheme } from "./hooks/useTheme";
import { t } from "./i18n/messages";
import "./App.css";

function AppContent() {
  const { pathname, navigate } = usePathname();
  const { locale, setLocale } = useLocale();
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  // Owned by the always-mounted shell so the conversation survives navigation
  // to the Corpus tab and back (BUG-2026-06-25, issue #53) and is write-through
  // to device-local `localStorage` (F33, ADR-023/024/025).
  const store = useConversationStore();
  const chat = useChatHistory(store);
  // Tag facets + selection lifted to the shell so the sidebar renders the topic
  // chips while ChatPanel consumes the selection for the ask request (D3).
  const tagFilters = useTagFilters();
  const onCorpus = pathname === "/corpus" || pathname.endsWith("/corpus");

  return (
    <div className="app-shell" data-sidebar-open={sidebarOpen}>
      <Sidebar
        open={sidebarOpen}
        locale={locale}
        theme={theme}
        onCorpus={onCorpus}
        newChatDisabled={chat.loading || chat.messages.length === 0}
        tags={tagFilters.tags}
        selectedTags={tagFilters.selected}
        previousChats={chat.previousChats}
        onNavigate={navigate}
        onNewChat={chat.newChat}
        onToggleTag={tagFilters.toggle}
        onSelectConversation={chat.selectConversation}
        onDeleteConversation={chat.deleteConversation}
        onClearAll={chat.clearAll}
        onSetLocale={setLocale}
        onToggleTheme={toggleTheme}
      />
      {sidebarOpen ? (
        <button
          type="button"
          className="sidebar-scrim"
          aria-hidden="true"
          tabIndex={-1}
          onClick={() => {
            setSidebarOpen(false);
          }}
        />
      ) : null}
      <div className="app-main">
        <header className="app-topbar" role="banner" data-testid="app-header">
          <button
            type="button"
            className="sidebar-toggle"
            aria-label={t(locale, "toggleSidebar")}
            aria-expanded={sidebarOpen}
            onClick={() => {
              setSidebarOpen((value) => !value);
            }}
          >
            <span aria-hidden="true">☰</span>
          </button>
          <div className="app-topbar-title">
            <h1>{t(locale, "appTitle")}</h1>
            <p className="subtitle">{t(locale, "appSubtitle")}</p>
          </div>
        </header>
        <main className="app">
          {onCorpus ? (
            <CorpusBrowse
              onNavigateHome={() => {
                navigate("/");
              }}
            />
          ) : (
            <ChatPanel chat={chat} selectedTags={tagFilters.selected} />
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <LocaleProvider>
      <AppContent />
    </LocaleProvider>
  );
}
