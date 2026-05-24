import { useCallback, useEffect, useState } from "react";

import { deleteDocument, listDocuments } from "../api/corpus";
import type { DocumentSummary } from "../api/types";
import { requireCorpusConfig } from "../config";
import { DocumentAdmin } from "./DocumentAdmin";

export function CorpusList() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentSummary | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const client = requireCorpusConfig();
      const list = await listDocuments(client);
      setDocuments(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load corpus");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleDelete = async (doc: DocumentSummary) => {
    const label = doc.title ?? doc.url;
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) {
      return;
    }
    setDeletingId(doc.document_id);
    setError(null);
    try {
      const client = requireCorpusConfig();
      await deleteDocument(client, doc.document_id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section aria-labelledby="corpus-heading">
      <h2 id="corpus-heading">Corpus documents</h2>
      {selected ? (
        <DocumentAdmin document={selected} onClose={() => setSelected(null)} />
      ) : (
        <>
          <button type="button" onClick={() => void refresh()} disabled={loading}>
            Refresh
          </button>
          {error ? (
            <p role="alert" className="error">
              {error}
            </p>
          ) : null}
          {loading ? (
            <p>Loading…</p>
          ) : documents.length === 0 ? (
            <p>No documents in corpus.</p>
          ) : (
            <ul className="corpus-list">
              {documents.map((doc) => (
                <li key={doc.document_id}>
                  <div>
                    <strong>{doc.title ?? "(untitled)"}</strong>
                    <br />
                    <a href={doc.url} target="_blank" rel="noreferrer">
                      {doc.url}
                    </a>
                    {doc.language ? <span> · {doc.language}</span> : null}
                  </div>
                  <div className="form-actions">
                    <button type="button" onClick={() => setSelected(doc)}>
                      Manage tags
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDelete(doc)}
                      disabled={deletingId === doc.document_id}
                    >
                      {deletingId === doc.document_id ? "Deleting…" : "Delete"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
