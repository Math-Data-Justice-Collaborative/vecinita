import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { type BulkResult, bulkUpdateMetadata } from "@/api/admin";
import { requireCorpusConfig } from "@/config";

interface BulkMetadataDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentIds: string[];
  onComplete: () => void;
}

export function BulkMetadataDialog({
  open,
  onOpenChange,
  documentIds,
  onComplete,
}: BulkMetadataDialogProps) {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BulkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    const updates: { title?: string; language?: string } = {};
    if (title.trim()) updates.title = title.trim();
    if (language.trim()) updates.language = language.trim();

    try {
      const client = requireCorpusConfig();
      const res = await bulkUpdateMetadata(client, documentIds, updates);
      setResult(res);
      if (res.failures.length === 0) {
        onOpenChange(false);
        onComplete();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Bulk metadata update failed",
      );
    } finally {
      setBusy(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    setTitle("");
    setLanguage("");
    onOpenChange(false);
    if (result && result.successes.length > 0) onComplete();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Bulk Edit Metadata</DialogTitle>
          <DialogDescription>
            Update metadata for {documentIds.length} document
            {documentIds.length !== 1 ? "s" : ""}. Leave fields empty to skip.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="bulk-title">Title</Label>
            <Input
              id="bulk-title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
              }}
              placeholder="New title (optional)"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="bulk-language">Language</Label>
            <Input
              id="bulk-language"
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value);
              }}
              placeholder="en, es, etc. (optional)"
            />
          </div>
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        {result && result.failures.length > 0 ? (
          <p className="text-sm text-destructive">
            {result.successes.length} updated, {result.failures.length} failed.
          </p>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={() => void handleSubmit()} disabled={busy}>
            {busy ? "Updating…" : "Update metadata"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
