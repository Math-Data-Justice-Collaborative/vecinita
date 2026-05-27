import { ChatPanel } from "./components/ChatPanel";
import { CorpusBrowse } from "./components/CorpusBrowse";
import { usePathname } from "./hooks/usePathname";
import "./App.css";

export default function App() {
  const { pathname, navigate } = usePathname();
  const onCorpus = pathname === "/corpus" || pathname.endsWith("/corpus");

  return (
    <main className="app">
      <header>
        <h1>Vecinita ChatRAG</h1>
        <p className="subtitle">
          Bilingual community Q&amp;A — answers stay in your browser only (F3).
        </p>
        <nav className="app-nav" aria-label="Primary">
          <button
            type="button"
            className={onCorpus ? "secondary" : undefined}
            onClick={() => { navigate("/"); }}
          >
            Chat
          </button>
          <button
            type="button"
            className={onCorpus ? undefined : "secondary"}
            onClick={() => { navigate("/corpus"); }}
          >
            Corpus
          </button>
        </nav>
      </header>
      {onCorpus ? (
        <CorpusBrowse onNavigateHome={() => { navigate("/"); }} />
      ) : (
        <ChatPanel />
      )}
    </main>
  );
}
