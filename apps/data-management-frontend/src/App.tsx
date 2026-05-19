import { CorpusList } from "./components/CorpusList";
import { JobForm } from "./components/JobForm";
import "./App.css";

export default function App() {
  return (
    <main className="app">
      <header>
        <h1>Vecinita Data Management</h1>
        <p className="subtitle">Ingest public URLs and manage the corpus (F12).</p>
      </header>
      <JobForm />
      <CorpusList />
    </main>
  );
}
