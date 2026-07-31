import { useState } from "react";

import { createJob } from "../api/jobs";
import type { CreateJobResponse, RebuildMode } from "../api/types";
import { requireAdminConfig } from "../config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";
import { useIsAdmin, useAuth } from "@/auth/auth-context";

export function RebuildForm() {
  const tr = useAdminT();
  const { loading: authLoading } = useAuth();
  const isAdmin = useIsAdmin();
  const [mode, setMode] = useState<RebuildMode>("rechunk");
  const [force, setForce] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<CreateJobResponse | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setCreated(null);
    setBusy(true);
    try {
      const client = requireAdminConfig();
      const response = await createJob(client, [], {
        job_type: "rebuild",
        mode,
        force,
        dry_run: dryRun,
      });
      setCreated(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("admin.rebuild.failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card data-testid="rebuild-form">
      <CardHeader>
        <CardTitle>{tr("admin.rebuild.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {authLoading ? (
          <p className="text-sm text-muted-foreground">
            {tr("shared.loading")}
          </p>
        ) : !isAdmin ? (
          <p
            className="text-sm text-muted-foreground"
            data-testid="rebuild-viewer-read-only"
          >
            {tr("admin.viewer.readOnlyNotice")}
          </p>
        ) : (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              {tr("admin.rebuild.description")}
            </p>
            <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="rebuild-mode">
                  {tr("admin.rebuild.modeLabel")}
                </Label>
                <select
                  id="rebuild-mode"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={mode}
                  disabled={busy}
                  data-testid="rebuild-mode"
                  onChange={(e) => {
                    const next = e.target.value;
                    if (
                      next === "reembed" ||
                      next === "rechunk" ||
                      next === "rescrape"
                    ) {
                      setMode(next);
                    }
                  }}
                >
                  <option value="reembed">
                    {tr("admin.rebuild.mode.reembed")}
                  </option>
                  <option value="rechunk">
                    {tr("admin.rebuild.mode.rechunk")}
                  </option>
                  <option value="rescrape">
                    {tr("admin.rebuild.mode.rescrape")}
                  </option>
                </select>
              </div>
              <div className="flex items-start gap-2">
                <input
                  id="rebuild-force"
                  type="checkbox"
                  className="mt-1"
                  checked={force}
                  disabled={busy}
                  data-testid="rebuild-force"
                  onChange={(e) => {
                    setForce(e.target.checked);
                  }}
                />
                <Label htmlFor="rebuild-force" className="font-normal">
                  {tr("admin.rebuild.forceLabel")}
                </Label>
              </div>
              <div className="flex items-start gap-2">
                <input
                  id="rebuild-dry-run"
                  type="checkbox"
                  className="mt-1"
                  checked={dryRun}
                  disabled={busy}
                  data-testid="rebuild-dry-run"
                  onChange={(e) => {
                    setDryRun(e.target.checked);
                  }}
                />
                <Label htmlFor="rebuild-dry-run" className="font-normal">
                  {tr("admin.rebuild.dryRunLabel")}
                </Label>
              </div>
              <Button
                type="submit"
                disabled={busy}
                data-testid="rebuild-submit"
              >
                {busy
                  ? tr("admin.rebuild.running")
                  : tr("admin.rebuild.submit")}
              </Button>
            </form>
            {error ? (
              <p role="alert" className="mt-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {created ? (
              <div
                className="mt-4 rounded-md bg-muted p-3"
                data-testid="rebuild-job-status"
              >
                <p className="text-sm">
                  {tr("admin.rebuild.jobStatusPrefix")}{" "}
                  <code className="font-mono text-xs">{created.job_id}</code>:{" "}
                  <strong>{created.status}</strong>
                </p>
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
