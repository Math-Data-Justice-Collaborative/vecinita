import { type FormEvent, useCallback, useEffect, useState } from "react";

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
import { useAdminT } from "@/hooks/useAdminT";
import { AdminWriteGate } from "@/components/AdminWriteGate";

type DocumentAdminProps = {
  document: DocumentSummary;
  onClose: () => void;
};

function parseTagsInput(raw: string): TagInput[] {
  return raw
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((slug) => ({
      slug,
      label: slug.replace(/-/g, " "),
      source: "human" as const,
    }));
}

export function DocumentAdmin({ document, onClose }: DocumentAdminProps) {
  const tr = useAdminT();
  const [chunks, setChunks] = useState<ChunkDetail[]>([]);
  const [docTags, setDocTags] = useState("");
  const [chunkTagDrafts, setChunkTagDrafts] = useState<Record<string, string>>(
    {},
  );
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
        Object.fromEntries(
          rows.map((chunk) => [chunk.chunk_id, tagsToInput(chunk.tags)]),
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.documentAdmin.loadChunksFailed"),
      );
    } finally {
      setLoading(false);
    }
  }, [document.document_id, tr]);

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
            setStatus(tr("admin.documentAdmin.retagCompleted"));
            setRetagJobId(null);
            void loadChunks();
            void loadDocumentTags();
          } else if (job.status === "failed") {
            setError(
              job.error_message ?? tr("admin.documentAdmin.retagFailed"),
            );
            setRetagJobId(null);
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(
              err instanceof Error
                ? err.message
                : tr("admin.documentAdmin.pollRetagFailed"),
            );
            setRetagJobId(null);
          }
        });
    }, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [retagJobId, loadChunks, loadDocumentTags, tr]);

  async function handleSaveDocumentTags(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const client = requireCorpusConfig();
      await patchDocumentTags(
        client,
        document.document_id,
        parseTagsInput(docTags),
      );
      setStatus(tr("admin.documentAdmin.docTagsSaved"));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.documentAdmin.saveDocTagsFailed"),
      );
    }
  }

  async function handleSaveChunkTags(chunkId: string) {
    setError(null);
    try {
      const client = requireCorpusConfig();
      await patchChunkTags(
        client,
        chunkId,
        parseTagsInput(chunkTagDrafts[chunkId] ?? ""),
      );
      setStatus(tr("admin.documentAdmin.chunkTagsSaved"));
      await loadChunks();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.documentAdmin.saveChunkTagsFailed"),
      );
    }
  }

  async function handleRetag() {
    setError(null);
    setStatus(null);
    try {
      const client = requireCorpusConfig();
      const jobId = await retagDocument(client, document.document_id);
      setRetagJobId(jobId);
      setStatus(tr("admin.documentAdmin.retagQueued", { jobId }));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.documentAdmin.queueRetagFailed"),
      );
    }
  }

  return (
    <div className="space-y-4" aria-label={tr("admin.documentAdmin.ariaLabel")}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {document.title ?? document.url}
        </h3>
        <Button variant="outline" size="sm" onClick={onClose}>
          {tr("admin.actions.close")}
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

      <AdminWriteGate>
        <form
          onSubmit={(e) => void handleSaveDocumentTags(e)}
          className="space-y-3"
        >
          <div className="space-y-2">
            <Label htmlFor="doc-tags">
              {tr("admin.documentAdmin.docTagsLabel")}
            </Label>
            <Input
              id="doc-tags"
              value={docTags}
              onChange={(e) => {
                setDocTags(e.target.value);
              }}
              placeholder={tr("admin.documentAdmin.docTagsPlaceholder")}
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm">
              {tr("admin.documentAdmin.saveDocTags")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void handleRetag()}
            >
              {tr("admin.documentAdmin.llmRetag")}
            </Button>
          </div>
        </form>
      </AdminWriteGate>

      <Separator />

      {loading ? (
        <p className="text-sm text-muted-foreground">
          {tr("admin.documentAdmin.loadingChunks")}
        </p>
      ) : null}

      <div className="space-y-4" data-testid="chunk-list">
        {chunks.map((chunk) => (
          <div key={chunk.chunk_id} className="space-y-2 rounded-md border p-4">
            <h4 className="font-medium">
              {tr("admin.documentAdmin.chunkTitle", {
                n: chunk.chunk_index + 1,
              })}
            </h4>
            <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-sm">
              {chunk.text}
            </pre>
            <div className="space-y-2">
              <Label htmlFor={`chunk-tags-${chunk.chunk_id}`}>
                {tr("admin.documentAdmin.chunkTagsLabel")}
              </Label>
              <Input
                id={`chunk-tags-${chunk.chunk_id}`}
                value={chunkTagDrafts[chunk.chunk_id] ?? ""}
                onChange={(e) => {
                  setChunkTagDrafts((current) => ({
                    ...current,
                    [chunk.chunk_id]: e.target.value,
                  }));
                }}
              />
            </div>
            <AdminWriteGate>
              <Button
                size="sm"
                variant="outline"
                onClick={() => void handleSaveChunkTags(chunk.chunk_id)}
              >
                {tr("admin.documentAdmin.saveChunkTags")}
              </Button>
            </AdminWriteGate>
          </div>
        ))}
      </div>
    </div>
  );
}

function tagsToInput(tags: TagInput[]): string {
  return tags.map((tag) => tag.slug).join(", ");
}
