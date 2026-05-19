import { ChatPanel } from "./components/ChatPanel";
import "./App.css";

export default function App() {
  return (
    <main className="app">
      <header>
        <h1>Vecinita ChatRAG</h1>
        <p className="subtitle">
          Bilingual community Q&amp;A — answers stay in your browser only (F3).
        </p>
      </header>
      <ChatPanel />
    </main>
  );
}
