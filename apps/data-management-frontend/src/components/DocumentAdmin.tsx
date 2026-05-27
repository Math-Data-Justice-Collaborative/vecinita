import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  listDocumentChunks,
  listDocumentTags,
  patchChunkTags,
  patchDocumentTags,
  retagDocument,
} from "../api/corpus";
import { getJob } from "../api/jobs";
import type { ChunkDetail, DocumentSummary, TagInput } from "../api/types";
import { requireAdminConfig, requireCorpusConfig } from "../config";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

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

  const loadDocumentTags = useCallback(async () => {
    try {
      const client = requireCorpusConfig();
      const tags = await listDocumentTags(client, document.document_id);
      setDocTags(tagsToInput(tags));
    } catch {
      // Non-fatal — document tags are supplementary to chunk view
    }
  }, [document.document_id]);

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
    void loadDocumentTags();
  }, [loadChunks, loadDocumentTags]);

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
            void loadDocumentTags();
          } else if (job.status === "failed") {
            setError(job.error_message ?? "Retag job failed");
            setRetagJobId(null);
          }
        })
        .catch((err: unknown) => {
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
  }, [retagJobId, loadChunks, loadDocumentTags]);

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
    <div className="space-y-4" aria-label="Document admin">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{document.title ?? document.url}</h3>
        <Button variant="outline" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {status ? (
        <p className="text-sm text-muted-foreground" role="status">
          {status}
        </p>
      ) : null}

      <form onSubmit={(e) => void handleSaveDocumentTags(e)} className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="doc-tags">Document tags (comma-separated slugs, max 10)</Label>
          <Input
            id="doc-tags"
            value={docTags}
            onChange={(e) => { setDocTags(e.target.value); }}
            placeholder="housing, legal"
          />
        </div>
        <div className="flex gap-2">
          <Button type="submit" size="sm">
            Save document tags
          </Button>
          <Button type="button" variant="secondary" size="sm" onClick={() => void handleRetag()}>
            LLM re-tag
          </Button>
        </div>
      </form>

      <Separator />

      {loading ? <p className="text-sm text-muted-foreground">Loading chunks…</p> : null}

      <div className="space-y-4" data-testid="chunk-list">
        {chunks.map((chunk) => (
          <div key={chunk.chunk_id} className="space-y-2 rounded-md border p-4">
            <h4 className="font-medium">Chunk {chunk.chunk_index + 1}</h4>
            <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-sm">{chunk.text}</pre>
            <div className="space-y-2">
              <Label htmlFor={`chunk-tags-${chunk.chunk_id}`}>Chunk tags (max 5)</Label>
              <Input
                id={`chunk-tags-${chunk.chunk_id}`}
                value={chunkTagDrafts[chunk.chunk_id] ?? ""}
                onChange={(e) =>
                  { setChunkTagDrafts((current) => ({
                    ...current,
                    [chunk.chunk_id]: e.target.value,
                  })); }
                }
              />
            </div>
            <Button size="sm" variant="outline" onClick={() => void handleSaveChunkTags(chunk.chunk_id)}>
              Save chunk tags
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

function tagsToInput(tags: TagInput[]): string {
  return tags.map((tag) => tag.slug).join(", ");
}
