import { ChatPanel } from "./components/ChatPanel";
import { CorpusBrowse } from "./components/CorpusBrowse";
import { LanguageToggle } from "./components/LanguageToggle";
import { LocaleProvider } from "./context/LocaleContext";
import { useChatHistory } from "./hooks/useChatHistory";
import { useConversationStore } from "./hooks/useConversationStore";
import { useLocale } from "./hooks/useLocale";
import { usePathname } from "./hooks/usePathname";
import { t } from "./i18n/messages";
import "./App.css";

function AppContent() {
  const { pathname, navigate } = usePathname();
  const { locale, setLocale } = useLocale();
  // Owned by the always-mounted shell so the conversation survives navigation
  // to the Corpus tab and back (BUG-2026-06-25, issue #53) and is write-through
  // to device-local `localStorage` so it survives refresh / tab-away, a tab
  // close, and is shared with new tabs (F33, ADR-023/024/025).
  const store = useConversationStore();
  const chat = useChatHistory(store);
  const onCorpus = pathname === "/corpus" || pathname.endsWith("/corpus");

  return (
    <div className="app-shell">
      <header className="app-header" role="banner" data-testid="app-header">
        <div className="app-header-main">
          <h1>{t(locale, "appTitle")}</h1>
          <p className="subtitle">{t(locale, "appSubtitle")}</p>
          <nav className="app-nav" aria-label="Primary">
            <button
              type="button"
              className={onCorpus ? "secondary" : undefined}
              onClick={() => {
                navigate("/");
              }}
            >
              {t(locale, "navChat")}
            </button>
            <button
              type="button"
              className={onCorpus ? undefined : "secondary"}
              onClick={() => {
                navigate("/corpus");
              }}
            >
              {t(locale, "navCorpus")}
            </button>
          </nav>
        </div>
        <LanguageToggle locale={locale} onChange={setLocale} />
      </header>
      <main className="app">
        {onCorpus ? (
          <CorpusBrowse
            onNavigateHome={() => {
              navigate("/");
            }}
          />
        ) : (
          <ChatPanel chat={chat} />
        )}
      </main>
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
