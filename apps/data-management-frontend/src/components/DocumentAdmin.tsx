import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  listDocumentChunks,
  patchChunkTags,
  patchDocumentTags,
  retagDocument,
} from "../api/corpus";
import { getJob } from "../api/jobs";
import type { ChunkDetail, DocumentSummary, TagInput } from "../api/types";
import { requireAdminConfig, requireCorpusConfig } from "../config";

type DocumentAdminProps = {
  document: DocumentSummary;
  onClose: () => void;
};

function parseTagsInput(raw: string): TagInput[] {
  return raw
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((slug) => ({ slug, label: slug.replace(/-/g, " "), source: "human" as const }));
}

export function DocumentAdmin({ document, onClose }: DocumentAdminProps) {
  const [chunks, setChunks] = useState<ChunkDetail[]>([]);
  const [docTags, setDocTags] = useState("");
  const [chunkTagDrafts, setChunkTagDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [retagJobId, setRetagJobId] = useState<string | null>(null);

  const loadChunks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const rows = await listDocumentChunks(client, document.document_id);
      setChunks(rows);
      setChunkTagDrafts(
        Object.fromEntries(rows.map((chunk) => [chunk.chunk_id, tagsToInput(chunk.tags)])),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chunks");
    } finally {
      setLoading(false);
    }
  }, [document.document_id]);

  useEffect(() => {
    void loadChunks();
  }, [loadChunks]);

  useEffect(() => {
    if (!retagJobId) {
      return;
    }
    let cancelled = false;
    const admin = requireAdminConfig();
    const timer = window.setInterval(() => {
      void getJob(admin, retagJobId)
        .then((job) => {
          if (cancelled) {
            return;
          }
          if (job.status === "completed") {
            setStatus("LLM re-tag job completed.");
            setRetagJobId(null);
            void loadChunks();
          } else if (job.status === "failed") {
            setError(job.error_message ?? "Retag job failed");
            setRetagJobId(null);
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "Failed to poll retag job");
            setRetagJobId(null);
          }
        });
    }, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [retagJobId, loadChunks]);

  async function handleSaveDocumentTags(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const client = requireCorpusConfig();
      await patchDocumentTags(client, document.document_id, parseTagsInput(docTags));
      setStatus("Document tags saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save document tags");
    }
  }

  async function handleSaveChunkTags(chunkId: string) {
    setError(null);
    try {
      const client = requireCorpusConfig();
      await patchChunkTags(client, chunkId, parseTagsInput(chunkTagDrafts[chunkId] ?? ""));
      setStatus("Chunk tags saved.");
      await loadChunks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save chunk tags");
    }
  }

  async function handleRetag() {
    setError(null);
    setStatus(null);
    try {
      const client = requireCorpusConfig();
      const jobId = await retagDocument(client, document.document_id);
      setRetagJobId(jobId);
      setStatus(`Retag job queued (${jobId}).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to queue retag job");
    }
  }

  return (
    <section className="document-admin" aria-label="Document admin">
      <div className="document-admin-header">
        <h2>{document.title ?? document.url}</h2>
        <button type="button" className="secondary" onClick={onClose}>
          Close
        </button>
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {status ? (
        <p className="status-hint" role="status">
          {status}
        </p>
      ) : null}

      <form className="tag-editor" onSubmit={(e) => void handleSaveDocumentTags(e)}>
        <label htmlFor="doc-tags">Document tags (comma-separated slugs, max 10)</label>
        <input
          id="doc-tags"
          value={docTags}
          onChange={(e) => setDocTags(e.target.value)}
          placeholder="housing, legal"
        />
        <div className="form-actions">
          <button type="submit">Save document tags</button>
          <button type="button" className="secondary" onClick={() => void handleRetag()}>
            LLM re-tag
          </button>
        </div>
      </form>

      {loading ? <p>Loading chunks…</p> : null}

      <ul className="chunk-list" data-testid="chunk-list">
        {chunks.map((chunk) => (
          <li key={chunk.chunk_id} className="chunk-item">
            <h3>Chunk {chunk.chunk_index + 1}</h3>
            <pre className="chunk-text">{chunk.text}</pre>
            <label htmlFor={`chunk-tags-${chunk.chunk_id}`}>Chunk tags (max 5)</label>
            <input
              id={`chunk-tags-${chunk.chunk_id}`}
              value={chunkTagDrafts[chunk.chunk_id] ?? ""}
              onChange={(e) =>
                setChunkTagDrafts((current) => ({
                  ...current,
                  [chunk.chunk_id]: e.target.value,
                }))
              }
            />
            <button type="button" onClick={() => void handleSaveChunkTags(chunk.chunk_id)}>
              Save chunk tags
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function tagsToInput(tags: TagInput[]): string {
  return tags.map((tag) => tag.slug).join(", ");
}
