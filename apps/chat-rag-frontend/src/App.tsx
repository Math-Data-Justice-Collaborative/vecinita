import { ChatPanel } from "./components/ChatPanel";
import { CorpusBrowse } from "./components/CorpusBrowse";
import { LanguageToggle } from "./components/LanguageToggle";
import { LocaleProvider } from "./context/LocaleContext";
import { useChatHistory } from "./hooks/useChatHistory";
import { useLocale } from "./hooks/useLocale";
import { usePathname } from "./hooks/usePathname";
import { t } from "./i18n/messages";
import "./App.css";

function AppContent() {
  const { pathname, navigate } = usePathname();
  const { locale, setLocale } = useLocale();
  // Owned by the always-mounted shell so the conversation survives navigation
  // to the Corpus tab and back (BUG-2026-06-25, issue #53).
  const chat = useChatHistory();
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
