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
import { type BulkResult, bulkTagDocuments } from "@/api/admin";
import { requireCorpusConfig } from "@/config";

interface BulkTagDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentIds: string[];
  onComplete: () => void;
}

export function BulkTagDialog({ open, onOpenChange, documentIds, onComplete }: BulkTagDialogProps) {
  const [addInput, setAddInput] = useState("");
  const [removeInput, setRemoveInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BulkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    const addTags = addInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((slug) => ({ slug, label: slug.replace(/-/g, " "), source: "human" as const }));
    const removeSlugs = removeInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      const client = requireCorpusConfig();
      const res = await bulkTagDocuments(client, documentIds, addTags, removeSlugs);
      setResult(res);
      if (res.failures.length === 0) {
        onOpenChange(false);
        onComplete();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk tag failed");
    } finally {
      setBusy(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    setAddInput("");
    setRemoveInput("");
    onOpenChange(false);
    if (result && result.successes.length > 0) onComplete();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Bulk Tag</DialogTitle>
          <DialogDescription>
            Add or remove tags for {documentIds.length} document{documentIds.length !== 1 ? "s" : ""}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="add-tags">Add tags (comma-separated)</Label>
            <Input id="add-tags" value={addInput} onChange={(e) => { setAddInput(e.target.value); }} placeholder="housing, legal" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="remove-tags">Remove tags (comma-separated slugs)</Label>
            <Input id="remove-tags" value={removeInput} onChange={(e) => { setRemoveInput(e.target.value); }} placeholder="outdated" />
          </div>
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        {result && result.failures.length > 0 ? (
          <p className="text-sm text-destructive">
            {result.successes.length} updated, {result.failures.length} failed.
          </p>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={busy}>Cancel</Button>
          <Button onClick={() => void handleSubmit()} disabled={busy}>
            {busy ? "Applying…" : "Apply tags"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
