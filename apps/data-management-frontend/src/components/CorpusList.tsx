import { useCallback, useEffect, useState } from "react";

import { deleteDocument, listDocuments } from "../api/corpus";
import type { DocumentSummary } from "../api/types";
import { requireCorpusConfig } from "../config";
import { DocumentAdmin } from "./DocumentAdmin";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Corpus Documents</CardTitle>
        <Button variant="outline" size="sm" onClick={() => void refresh()} disabled={loading}>
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {selected ? (
          <DocumentAdmin document={selected} onClose={() => setSelected(null)} />
        ) : (
          <>
            {error ? (
              <p role="alert" className="mb-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No documents in corpus.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Language</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((doc) => (
                    <TableRow key={doc.document_id}>
                      <TableCell className="font-medium">{doc.title ?? "(untitled)"}</TableCell>
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
                      <TableCell>{doc.language ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => setSelected(doc)}>
                            Manage tags
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => void handleDelete(doc)}
                            disabled={deletingId === doc.document_id}
                          >
                            {deletingId === doc.document_id ? "Deleting…" : "Delete"}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
