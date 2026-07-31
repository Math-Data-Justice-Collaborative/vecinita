import { useState } from "react";

import { createJob } from "../api/jobs";
import type { BackfillSource, CreateJobResponse } from "../api/types";
import { requireAdminConfig } from "../config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";
import { useIsAdmin, useAuth } from "@/auth/auth-context";

export function BackfillForm() {
  const tr = useAdminT();
  const { loading: authLoading } = useAuth();
  const isAdmin = useIsAdmin();
  const [source, setSource] = useState<BackfillSource>("rescrape");
  const [ackFromChunks, setAckFromChunks] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<CreateJobResponse | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setCreated(null);

    if (source === "from_chunks" && !ackFromChunks) {
      setError(tr("admin.backfill.validation.ackRequired"));
      return;
    }

    setBusy(true);
    try {
      const client = requireAdminConfig();
      const response = await createJob(client, [], {
        job_type: "rebuild",
        mode: source === "from_chunks" ? "rechunk" : "rescrape",
        backfill: true,
        backfill_source: source,
        ...(source === "from_chunks"
          ? { ack_reconstruct_from_chunks: true }
          : {}),
      });
      setCreated(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.backfill.failed"),
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card data-testid="backfill-form">
      <CardHeader>
        <CardTitle>{tr("admin.backfill.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {authLoading ? (
          <p className="text-sm text-muted-foreground">
            {tr("shared.loading")}
          </p>
        ) : !isAdmin ? (
          <p
            className="text-sm text-muted-foreground"
            data-testid="backfill-viewer-read-only"
          >
            {tr("admin.viewer.readOnlyNotice")}
          </p>
        ) : (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              {tr("admin.backfill.description")}
            </p>
            <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="backfill-source">
                  {tr("admin.backfill.sourceLabel")}
                </Label>
                <select
                  id="backfill-source"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={source}
                  disabled={busy}
                  onChange={(e) => {
                    const next = e.target.value;
                    if (next === "rescrape" || next === "from_chunks") {
                      setSource(next);
                      if (next === "rescrape") {
                        setAckFromChunks(false);
                      }
                    }
                  }}
                >
                  <option value="rescrape">
                    {tr("admin.backfill.source.rescrape")}
                  </option>
                  <option value="from_chunks">
                    {tr("admin.backfill.source.fromChunks")}
                  </option>
                </select>
              </div>
              {source === "from_chunks" ? (
                <div className="flex items-start gap-2">
                  <input
                    id="backfill-ack"
                    type="checkbox"
                    className="mt-1"
                    checked={ackFromChunks}
                    disabled={busy}
                    data-testid="backfill-ack"
                    onChange={(e) => {
                      setAckFromChunks(e.target.checked);
                    }}
                  />
                  <Label htmlFor="backfill-ack" className="font-normal">
                    {tr("admin.backfill.ackLabel")}
                  </Label>
                </div>
              ) : null}
              <Button
                type="submit"
                disabled={busy}
                data-testid="backfill-submit"
              >
                {busy
                  ? tr("admin.backfill.running")
                  : tr("admin.backfill.submit")}
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
                data-testid="backfill-job-status"
              >
                <p className="text-sm">
                  {tr("admin.backfill.jobStatusPrefix")}{" "}
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
