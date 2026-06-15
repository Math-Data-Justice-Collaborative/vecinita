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
import { useAdminT } from "@/hooks/useAdminT";

interface BulkTagDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentIds: string[];
  onComplete: () => void;
}

export function BulkTagDialog({
  open,
  onOpenChange,
  documentIds,
  onComplete,
}: BulkTagDialogProps) {
  const tr = useAdminT();
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
      .map((slug) => ({
        slug,
        label: slug.replace(/-/g, " "),
        source: "human" as const,
      }));
    const removeSlugs = removeInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      const client = requireCorpusConfig();
      const res = await bulkTagDocuments(
        client,
        documentIds,
        addTags,
        removeSlugs,
      );
      setResult(res);
      if (res.failures.length === 0) {
        onOpenChange(false);
        onComplete();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("admin.bulkTag.failed"));
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
          <DialogTitle>{tr("admin.bulkTag.title")}</DialogTitle>
          <DialogDescription>
            {tr("admin.bulkTag.description", { n: documentIds.length })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="add-tags">{tr("admin.bulkTag.addLabel")}</Label>
            <Input
              id="add-tags"
              value={addInput}
              onChange={(e) => {
                setAddInput(e.target.value);
              }}
              placeholder={tr("admin.bulkTag.addPlaceholder")}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="remove-tags">
              {tr("admin.bulkTag.removeLabel")}
            </Label>
            <Input
              id="remove-tags"
              value={removeInput}
              onChange={(e) => {
                setRemoveInput(e.target.value);
              }}
              placeholder={tr("admin.bulkTag.removePlaceholder")}
            />
          </div>
        </div>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        {result && result.failures.length > 0 ? (
          <p className="text-sm text-destructive">
            {tr("admin.bulk.partialFailureSummary", {
              updated: result.successes.length,
              failed: result.failures.length,
            })}
          </p>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={busy}>
            {tr("shared.cancel")}
          </Button>
          <Button onClick={() => void handleSubmit()} disabled={busy}>
            {busy ? tr("admin.bulkTag.applying") : tr("admin.bulkTag.apply")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
