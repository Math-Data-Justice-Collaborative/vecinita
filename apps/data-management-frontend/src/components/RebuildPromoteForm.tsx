import { useState } from "react";

import {
  promoteRebuildRun,
  type RebuildPromoteResponseApi,
} from "../api/admin";
import { requireCorpusConfig } from "../config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";
import { useIsAdmin, useAuth } from "@/auth/auth-context";

export function RebuildPromoteForm() {
  const tr = useAdminT();
  const { loading: authLoading } = useAuth();
  const isAdmin = useIsAdmin();
  const [runId, setRunId] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RebuildPromoteResponseApi | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    const trimmed = runId.trim();
    if (!trimmed) {
      setError(tr("admin.rebuild.promote.validation.runId"));
      return;
    }
    if (!confirmed) {
      setError(tr("admin.rebuild.promote.validation.confirmRequired"));
      return;
    }

    setBusy(true);
    try {
      const client = requireCorpusConfig();
      const response = await promoteRebuildRun(client, trimmed);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.rebuild.promote.failed"),
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card data-testid="rebuild-promote-form">
      <CardHeader>
        <CardTitle>{tr("admin.rebuild.promote.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {authLoading ? (
          <p className="text-sm text-muted-foreground">
            {tr("shared.loading")}
          </p>
        ) : !isAdmin ? (
          <p
            className="text-sm text-muted-foreground"
            data-testid="rebuild-promote-viewer-read-only"
          >
            {tr("admin.viewer.readOnlyNotice")}
          </p>
        ) : (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              {tr("admin.rebuild.promote.description")}
            </p>
            <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="rebuild-promote-run-id">
                  {tr("admin.rebuild.promote.runIdLabel")}
                </Label>
                <Input
                  id="rebuild-promote-run-id"
                  value={runId}
                  disabled={busy}
                  data-testid="rebuild-promote-run-id"
                  placeholder={tr("admin.rebuild.promote.runIdPlaceholder")}
                  onChange={(e) => {
                    setRunId(e.target.value);
                  }}
                />
              </div>
              <div className="flex items-start gap-2">
                <input
                  id="rebuild-promote-confirm"
                  type="checkbox"
                  className="mt-1"
                  checked={confirmed}
                  disabled={busy}
                  data-testid="rebuild-promote-confirm"
                  onChange={(e) => {
                    setConfirmed(e.target.checked);
                  }}
                />
                <Label
                  htmlFor="rebuild-promote-confirm"
                  className="font-normal"
                >
                  {tr("admin.rebuild.promote.confirmLabel")}
                </Label>
              </div>
              <Button
                type="submit"
                disabled={busy}
                data-testid="rebuild-promote-submit"
              >
                {busy
                  ? tr("admin.rebuild.promote.running")
                  : tr("admin.rebuild.promote.submit")}
              </Button>
            </form>
            {error ? (
              <p role="alert" className="mt-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {result ? (
              <div
                className="mt-4 rounded-md bg-muted p-3"
                data-testid="rebuild-promote-result"
              >
                <p className="text-sm">
                  {tr("admin.rebuild.promote.resultPrefix")}{" "}
                  <code className="font-mono text-xs">
                    {result.rebuild_run_id}
                  </code>
                  : {String(result.chunks_promoted)}{" "}
                  {tr("admin.rebuild.promote.chunksLabel")},{" "}
                  {String(result.documents_promoted)}{" "}
                  {tr("admin.rebuild.promote.documentsLabel")}
                </p>
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
