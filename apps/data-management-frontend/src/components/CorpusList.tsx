import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActionIcon, PaginationControls } from "vecinita-frontend-ui";

import { deleteDocument, fetchCorpusTree, listDocuments } from "../api/corpus";
import type { DocumentSummary, TreeNode } from "../api/types";
import { requireCorpusConfig } from "../config";
import { DocumentAdmin } from "./DocumentAdmin";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import { Label } from "@/components/ui/label";
import { BulkDeleteDialog } from "@/components/BulkDeleteDialog";
import { BulkTagDialog } from "@/components/BulkTagDialog";
import { BulkMetadataDialog } from "@/components/BulkMetadataDialog";
import { CorpusTree } from "@/components/CorpusTree";
import { TruncatedText } from "@/components/TruncatedText";
import { BoundedTagList } from "@/components/BoundedTagList";
import { ParityBadge } from "@/components/ParityBadge";
import { RefreshCw, Trash2, Tags, FileEdit } from "lucide-react";
import { useAdminT } from "@/hooks/useAdminT";
import { useIsAdmin } from "@/auth/auth-context";
import { cn } from "@/lib/utils";

const DEFAULT_PAGE_SIZE = 50;

type CorpusViewMode = "flat" | "tree";

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
  const [treeRoots, setTreeRoots] = useState<TreeNode[]>([]);
  const [viewMode, setViewMode] = useState<CorpusViewMode>("flat");
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
  const [staleOnly, setStaleOnly] = useState(false);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / DEFAULT_PAGE_SIZE)),
    [total],
  );

  const refresh = useCallback(
    async (isActive: () => boolean, nextPage = 1, filterStale = staleOnly) => {
      setError(null);
      setLoading(true);
      try {
        const client = requireCorpusConfig();
        const result = await listDocuments(client, {
          page: nextPage,
          pageSize: DEFAULT_PAGE_SIZE,
          ...(filterStale ? { stale: true } : {}),
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
    [staleOnly],
  );

  const refreshTree = useCallback(async (isActive: () => boolean) => {
    setError(null);
    setLoading(true);
    try {
      const client = requireCorpusConfig();
      const result = await fetchCorpusTree(client);
      /* v8 ignore next -- unmount race */
      if (!isActive()) {
        return;
      }
      setTreeRoots(result.roots);
      setSelectedIds(new Set());
    } catch (err) {
      /* v8 ignore next -- unmount race */
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
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (viewMode === "tree") {
      void refreshTree(() => !cancelled);
    } else {
      void refresh(() => !cancelled, page);
    }
    return () => {
      cancelled = true;
    };
  }, [refresh, refreshTree, page, viewMode, staleOnly]);

  const handleStaleFilterChange = (next: boolean) => {
    setStaleOnly(next);
    setPage(1);
  };

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
      // Row delete exists only in flat table; always refresh the list page.
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

  const handleRefreshClick = () => {
    if (viewMode === "tree") {
      void refreshTree(() => true);
    } else {
      void refresh(() => true, page);
    }
  };

  const refreshAfterBulk = () => {
    if (viewMode === "tree") {
      void refreshTree(() => true);
    } else {
      void refresh(() => true, page);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle>{tr("admin.corpusList.title")}</CardTitle>
        <div className="flex items-center gap-2">
          <div
            className="flex rounded-md border border-border p-0.5"
            role="group"
            aria-label={tr("admin.corpusTree.ariaLabel")}
          >
            <Button
              type="button"
              variant={viewMode === "flat" ? "secondary" : "ghost"}
              size="sm"
              data-testid="corpus-view-flat"
              onClick={() => {
                setViewMode("flat");
              }}
            >
              {tr("admin.corpusTree.viewFlat")}
            </Button>
            <Button
              type="button"
              variant={viewMode === "tree" ? "secondary" : "ghost"}
              size="sm"
              data-testid="corpus-view-tree"
              onClick={() => {
                setViewMode("tree");
              }}
            >
              {tr("admin.corpusTree.viewTree")}
            </Button>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshClick}
            disabled={loading}
            data-testid="corpus-refresh"
            aria-label={tr("shared.refresh")}
          >
            <ActionIcon
              motion="spin"
              pending={loading}
              className="mr-2 inline-flex"
              data-testid="corpus-refresh-icon"
            >
              <RefreshCw className="h-4 w-4" />
            </ActionIcon>
            {tr("shared.refresh")}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {selected ? (
          <DocumentAdmin
            document={selected}
            onClose={() => {
              setSelected(null);
            }}
            onChanged={() => {
              void refresh(() => true, page);
            }}
          />
        ) : (
          <>
            {viewMode === "flat" ? (
              <div className="mb-4 flex items-center gap-2">
                <Checkbox
                  id="corpus-stale-filter"
                  checked={staleOnly}
                  onCheckedChange={(value) => {
                    handleStaleFilterChange(value === true);
                  }}
                  data-testid="corpus-stale-filter"
                />
                <Label htmlFor="corpus-stale-filter">
                  {tr("admin.corpusList.staleFilter")}
                </Label>
              </div>
            ) : null}
            {selectedIds.size > 0 && isAdmin && (
              <div
                data-testid="bulk-toolbar"
                className="sticky top-0 z-20 mb-4 flex items-center gap-2 rounded-md border border-border bg-muted p-2 contrast-more:border-foreground"
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
            ) : viewMode === "tree" ? (
              <CorpusTree
                roots={treeRoots}
                selectedIds={selectedIds}
                onToggleSelect={toggleId}
              />
            ) : documents.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {tr("admin.corpusList.empty")}
              </p>
            ) : (
              <Table
                className="table-fixed"
                containerClassName="max-h-[min(60vh,32rem)] rounded-md border border-border contrast-more:border-foreground"
                containerTestId="corpus-table-scroll"
              >
                <TableHeader className="sticky top-0 z-10 bg-background shadow-sm [&_tr]:border-b">
                  <TableRow>
                    {isAdmin ? (
                      <TableHead className="w-10 bg-background">
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
                    <TableHead
                      className={cn(
                        "bg-background",
                        isAdmin ? "w-[32%]" : "w-[40%]",
                      )}
                    >
                      {tr("admin.corpusList.columnTitle")}
                    </TableHead>
                    <TableHead
                      className={cn(
                        "bg-background",
                        isAdmin ? "w-[28%]" : "w-[40%]",
                      )}
                    >
                      {tr("admin.corpusList.columnUrl")}
                    </TableHead>
                    <TableHead className="w-20 bg-background">
                      {tr("admin.corpusList.columnLanguage")}
                    </TableHead>
                    <TableHead className="w-36 bg-background">
                      {tr("admin.corpusList.columnFreshness")}
                    </TableHead>
                    {isAdmin ? (
                      <TableHead className="w-44 bg-background text-right">
                        {tr("admin.corpusList.columnActions")}
                      </TableHead>
                    ) : null}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((doc) => {
                    const displayTitle =
                      doc.display_title ??
                      doc.title ??
                      tr("admin.corpusList.untitled");
                    return (
                      <TableRow
                        key={doc.document_id}
                        data-state={
                          selectedIds.has(doc.document_id)
                            ? "selected"
                            : undefined
                        }
                      >
                        {isAdmin ? (
                          <TableCell className="py-2">
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
                        <TableCell className="max-w-0 py-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <TruncatedText
                              text={displayTitle}
                              className="font-medium"
                              data-testid={`corpus-title-${doc.document_id}`}
                            />
                            {doc.stale ? (
                              <Badge
                                variant="destructive"
                                data-testid={`corpus-stale-badge-${doc.document_id}`}
                              >
                                {tr("admin.corpusList.staleBadge")}
                              </Badge>
                            ) : null}
                          </div>
                          {doc.tags && doc.tags.length > 0 ? (
                            <BoundedTagList
                              tags={doc.tags}
                              moreTestId={`corpus-tags-more-${doc.document_id}`}
                            />
                          ) : null}
                        </TableCell>
                        <TableCell className="max-w-0 py-2">
                          <TruncatedText
                            as="a"
                            href={doc.url}
                            text={doc.url}
                            target="_blank"
                            rel="noreferrer"
                            data-testid={`corpus-url-${doc.document_id}`}
                          />
                        </TableCell>
                        <TableCell className="py-2">
                          <div className="flex flex-col">
                            <span>{doc.language ?? tr("shared.emDash")}</span>
                            <ParityBadge document={doc} />
                          </div>
                        </TableCell>
                        <TableCell className="py-2 text-xs text-muted-foreground">
                          <span
                            data-testid={`corpus-last-checked-${doc.document_id}`}
                          >
                            {doc.last_checked_at
                              ? tr("admin.corpusList.lastChecked", {
                                  when: doc.last_checked_at.slice(0, 10),
                                })
                              : tr("admin.corpusList.lastCheckedNever")}
                          </span>
                        </TableCell>
                        {isAdmin ? (
                          <TableCell className="py-2 text-right">
                            <div className="flex justify-end gap-2 whitespace-nowrap">
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
                    );
                  })}
                </TableBody>
              </Table>
            )}

            {!loading && viewMode === "flat" && total > 0 ? (
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
              onComplete={refreshAfterBulk}
            />
            <BulkTagDialog
              open={bulkTagOpen}
              onOpenChange={setBulkTagOpen}
              documentIds={selectionArray}
              onComplete={refreshAfterBulk}
            />
            <BulkMetadataDialog
              open={bulkMetadataOpen}
              onOpenChange={setBulkMetadataOpen}
              documentIds={selectionArray}
              onComplete={refreshAfterBulk}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
