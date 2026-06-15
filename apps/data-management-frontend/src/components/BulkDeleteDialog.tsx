import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { type BulkResult, bulkDeleteDocuments } from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";

interface BulkDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  documentIds: string[];
  onComplete: () => void;
}

export function BulkDeleteDialog({
  open,
  onOpenChange,
  documentIds,
  onComplete,
}: BulkDeleteDialogProps) {
  const tr = useAdminT();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BulkResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setBusy(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const res = await bulkDeleteDocuments(client, documentIds);
      setResult(res);
      if (res.failures.length === 0) {
        onOpenChange(false);
        onComplete();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.bulkDelete.failed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    onOpenChange(false);
    if (result && result.successes.length > 0) {
      onComplete();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{tr("admin.bulkDelete.title")}</DialogTitle>
          <DialogDescription>
            {tr("admin.bulkDelete.description", { n: documentIds.length })}
          </DialogDescription>
        </DialogHeader>

        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        {result && result.failures.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm">
              {tr("admin.bulkDelete.partialFailureHeader", {
                deleted: result.successes.length,
                failed: result.failures.length,
              })}
            </p>
            <ul className="text-sm text-destructive">
              {result.failures.map((f) => (
                <li key={f.document_id}>
                  {f.document_id}: {f.error}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={busy}>
            {tr("shared.cancel")}
          </Button>
          <Button
            variant="destructive"
            onClick={() => void handleConfirm()}
            disabled={busy}
          >
            {busy
              ? tr("admin.actions.deleting")
              : tr("admin.bulkDelete.confirm")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
