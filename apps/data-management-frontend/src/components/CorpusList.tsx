import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { PaginationControls } from "vecinita-frontend-ui";

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
import { useIsAdmin } from "@/auth/auth-context";

const DEFAULT_PAGE_SIZE = 50;

export function CorpusList() {
  const tr = useAdminT();
  const isAdmin = useIsAdmin();
  // Keep the load path decoupled from `tr`: its identity changes on every
  // EN/ES switch, and depending on it would refire the mount loader and clear
  // the bulk selection on a locale change (BUG-2026-06-25).
  const trRef = useRef(tr);
  useEffect(() => {
    trRef.current = tr;
  }, [tr]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentSummary | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkTagOpen, setBulkTagOpen] = useState(false);
  const [bulkMetadataOpen, setBulkMetadataOpen] = useState(false);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / DEFAULT_PAGE_SIZE)),
    [total],
  );

  const refresh = useCallback(
    async (isActive: () => boolean, nextPage = 1) => {
      setError(null);
      setLoading(true);
      try {
        const client = requireCorpusConfig();
        const result = await listDocuments(client, {
          page: nextPage,
          pageSize: DEFAULT_PAGE_SIZE,
        });
        if (!isActive()) {
          return;
        }
        setDocuments(result.items);
        setTotal(result.total);
        setPage(result.page);
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
    void refresh(() => !cancelled, page);
    return () => {
      cancelled = true;
    };
  }, [refresh, page]);

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
      await refresh(() => true, page);
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

  /** Select-all is page-scoped (BUG-2026-07-28 / #112). */
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
          onClick={() => void refresh(() => true, page)}
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
            {selectedIds.size > 0 && isAdmin && (
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
                    {isAdmin ? (
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
                    ) : null}
                    <TableHead>{tr("admin.corpusList.columnTitle")}</TableHead>
                    <TableHead>{tr("admin.corpusList.columnUrl")}</TableHead>
                    <TableHead>
                      {tr("admin.corpusList.columnLanguage")}
                    </TableHead>
                    {isAdmin ? (
                      <TableHead className="text-right">
                        {tr("admin.corpusList.columnActions")}
                      </TableHead>
                    ) : null}
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
                      {isAdmin ? (
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
                      ) : null}
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
                      {isAdmin ? (
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
                      ) : null}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            {!loading && total > 0 ? (
              <div className="mt-4">
                <PaginationControls
                  page={page}
                  totalPages={totalPages}
                  total={total}
                  previousDisabled={page <= 1}
                  nextDisabled={page >= totalPages}
                  onPrevious={() => {
                    setPage((current) => Math.max(1, current - 1));
                  }}
                  onNext={() => {
                    setPage((current) => Math.min(totalPages, current + 1));
                  }}
                />
              </div>
            ) : null}

            <BulkDeleteDialog
              open={bulkDeleteOpen}
              onOpenChange={setBulkDeleteOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh(() => true, page)}
            />
            <BulkTagDialog
              open={bulkTagOpen}
              onOpenChange={setBulkTagOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh(() => true, page)}
            />
            <BulkMetadataDialog
              open={bulkMetadataOpen}
              onOpenChange={setBulkMetadataOpen}
              documentIds={selectionArray}
              onComplete={() => void refresh(() => true, page)}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
