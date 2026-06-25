import { useCallback, useEffect, useRef, useState } from "react";

import { deleteDocument, listDocuments } from "../api/corpus";
import type { DocumentSummary } from "../api/types";
import { requireCorpusConfig } from "../config";
import { DocumentAdmin } from "./DocumentAdmin";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { TagBadge } from "@/components/TagBadge";
import { BulkDeleteDialog } from "@/components/BulkDeleteDialog";
import { BulkTagDialog } from "@/components/BulkTagDialog";
import { BulkMetadataDialog } from "@/components/BulkMetadataDialog";
import { Trash2, Tags, FileEdit } from "lucide-react";
import { useAdminT } from "@/hooks/useAdminT";

export function CorpusList() {
  const tr = useAdminT();
  // Keep the load path decoupled from `tr`: its identity changes on every
  // EN/ES switch, and depending on it would refire the mount loader and clear
  // the bulk selection on a locale change (BUG-2026-06-25).
  const trRef = useRef(tr);
  useEffect(() => {
    trRef.current = tr;
  }, [tr]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentSummary | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkTagOpen, setBulkTagOpen] = useState(false);
  const [bulkMetadataOpen, setBulkMetadataOpen] = useState(false);

  const refresh = useCallback(
    async (isActive: () => boolean = () => true) => {
      setError(null);
      setLoading(true);
      try {
        const client = requireCorpusConfig();
        const list = await listDocuments(client);
        if (!isActive()) {
          return;
        }
        setDocuments(list);
        setSelectedIds(new Set());
      } catch (err) {
        if (!isActive()) {
          return;
        }
        setError(
          err instanceof Error
            ? err.message
            : trRef.current("admin.corpusList.loadFailed"),
        );
      } finally {
        if (isActive()) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;
    void refresh(() => !cancelled);
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const handleDelete = async (doc: DocumentSummary) => {
    const label = doc.title ?? doc.url;
    if (!window.confirm(tr("admin.corpusList.deleteConfirm", { label }))) {
      return;
    }
    setDeletingId(doc.document_id);
    setError(null);
    try {
      const client = requireCorpusConfig();
      await deleteDocument(client, doc.document_id);
      await refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.corpusList.deleteFailed"),
      );
    } finally {
      setDeletingId(null);
    }
  };

  const toggleId = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === documents.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(documents.map((d) => d.document_id)));
    }
  };

  const selectionArray = Array.from(selectedIds);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{tr("admin.corpusList.title")}</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void refresh()}
          disabled={loading}
        >
          {tr("shared.refresh")}
        </Button>
      </CardHeader>
      <CardContent>
        {selected ? (
          <DocumentAdmin
            document={selected}
            onClose={() => {
              setSelected(null);
            }}
          />
        ) : (
          <>
            {selectedIds.size > 0 && (
              <div
                data-testid="bulk-toolbar"
                className="mb-4 flex items-center gap-2 rounded-md border bg-muted p-2"
              >
                <span className="text-sm font-medium">
                  {tr("admin.corpusList.selectedCount", {
                    count: selectedIds.size,
                  })}
                </span>
                <Button
                  variant="destructive"
                  size="sm"
                  data-testid="bulk-delete-btn"
                  onClick={() => {
                    setBulkDeleteOpen(true);
                  }}
                >
                  <Trash2 className="mr-1 h-4 w-4" />
                  {tr("admin.actions.delete")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  data-testid="bulk-tag-btn"
                  onClick={() => {
                    setBulkTagOpen(true);
                  }}
                >
                  <Tags className="mr-1 h-4 w-4" />
                  {tr("admin.actions.tag")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  data-testid="bulk-metadata-btn"
                  onClick={() => {
                    setBulkMetadataOpen(true);
                  }}
                >
                  <FileEdit className="mr-1 h-4 w-4" />
                  {tr("admin.actions.metadata")}
                </Button>
              </div>
            )}

            {error ? (
              <p role="alert" className="mb-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {loading ? (
              <p className="text-sm text-muted-foreground">
                {tr("shared.loading")}
              </p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {tr("admin.corpusList.empty")}
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">
                      <Checkbox
                        data-testid="select-all"
                        checked={
                          selectedIds.size === documents.length &&
                          documents.length > 0
                        }
                        onCheckedChange={toggleAll}
                        aria-label={tr("admin.corpusList.selectAll")}
                      />
                    </TableHead>
                    <TableHead>{tr("admin.corpusList.columnTitle")}</TableHead>
                    <TableHead>{tr("admin.corpusList.columnUrl")}</TableHead>
                    <TableHead>
                      {tr("admin.corpusList.columnLanguage")}
                    </TableHead>
                    <TableHead className="text-right">
                      {tr("admin.corpusList.columnActions")}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((doc) => (
                    <TableRow
                      key={doc.document_id}
                      data-state={
                        selectedIds.has(doc.document_id)
                          ? "selected"
                          : undefined
                      }
                    >
                      <TableCell>
                        <Checkbox
                          checked={selectedIds.has(doc.document_id)}
                          onCheckedChange={() => {
                            toggleId(doc.document_id);
                          }}
                          aria-label={tr("admin.corpusList.selectRow", {
                            label: doc.title ?? doc.url,
                          })}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {doc.title ?? tr("admin.corpusList.untitled")}
                        </div>
                        {doc.tags && doc.tags.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {doc.tags.map((tag) => (
                              <TagBadge key={tag.slug} tag={tag} />
                            ))}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <a
                          href={doc.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-primary underline-offset-4 hover:underline"
                        >
                          {doc.url}
                        </a>
                      </TableCell>
                      <TableCell>
                        {doc.language ?? tr("shared.emDash")}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelected(doc);
                            }}
                          >
                            {tr("admin.corpusList.manageTags")}
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => void handleDelete(doc)}
                            disabled={deletingId === doc.document_id}
                          >
                            {deletingId === doc.document_id
                              ? tr("admin.actions.deleting")
                              : tr("admin.actions.delete")}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            <BulkDeleteDialog
              open={bulkDeleteOpen}
              onOpenChange={setBulkDeleteOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh()}
            />
            <BulkTagDialog
              open={bulkTagOpen}
              onOpenChange={setBulkTagOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh()}
            />
            <BulkMetadataDialog
              open={bulkMetadataOpen}
              onOpenChange={setBulkMetadataOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh()}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
