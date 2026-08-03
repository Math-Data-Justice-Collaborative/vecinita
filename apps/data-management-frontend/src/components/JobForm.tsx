import { useCallback, useState } from "react";

import { createJob, getJob, parseUrlsInput } from "../api/jobs";
import type { CreateJobOptions, Job } from "../api/types";
import { requireAdminConfig } from "../config";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminT } from "@/hooks/useAdminT";
import { useIsAdmin, useAuth } from "@/auth/auth-context";

const POLL_MS = 2000;
const TERMINAL: Job["status"][] = ["completed", "failed"];
const DEFAULT_MAX_DEPTH = 2;
const DEFAULT_MAX_PAGES = 25;

export interface JobFormProps {
  onJobUpdate?: (job: Job) => void;
}

export function JobForm({ onJobUpdate }: JobFormProps) {
  const tr = useAdminT();
  const { loading: authLoading } = useAuth();
  const isAdmin = useIsAdmin();
  const [urlsText, setUrlsText] = useState("");
  const [chunkSize, setChunkSize] = useState("256");
  const [crawl, setCrawl] = useState(false);
  const [maxDepth, setMaxDepth] = useState(String(DEFAULT_MAX_DEPTH));
  const [maxPages, setMaxPages] = useState(String(DEFAULT_MAX_PAGES));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<Job | null>(null);

  const pollUntilDone = useCallback(
    async (jobId: string) => {
      const client = requireAdminConfig();
      let job = await getJob(client, jobId);
      setActiveJob(job);
      onJobUpdate?.(job);

      while (!TERMINAL.includes(job.status)) {
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        job = await getJob(client, jobId);
        setActiveJob(job);
        onJobUpdate?.(job);
      }
    },
    [onJobUpdate],
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setActiveJob(null);

    const urls = parseUrlsInput(urlsText);
    if (urls.length === 0) {
      setError(tr("admin.ingest.validation.noUrls"));
      return;
    }

    const parsedChunk = Number(chunkSize);
    if (!Number.isFinite(parsedChunk) || parsedChunk < 64) {
      setError(tr("admin.ingest.validation.chunkSizeMin"));
      return;
    }

    const options: CreateJobOptions = { chunk_size_tokens: parsedChunk };
    if (crawl) {
      const parsedDepth = Number(maxDepth);
      if (!Number.isFinite(parsedDepth) || parsedDepth < 0) {
        setError(tr("admin.ingest.validation.maxDepthMin"));
        return;
      }
      const parsedPages = Number(maxPages);
      if (!Number.isFinite(parsedPages) || parsedPages < 1) {
        setError(tr("admin.ingest.validation.maxPagesMin"));
        return;
      }
      options.crawl = true;
      options.max_depth = parsedDepth;
      options.max_pages = parsedPages;
      options.crawl_scope = "same_domain";
    }

    setBusy(true);
    try {
      const client = requireAdminConfig();
      const created = await createJob(client, urls, options);
      await pollUntilDone(created.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("admin.ingest.failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{tr("admin.ingest.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {authLoading ? (
          <p className="text-sm text-muted-foreground">
            {tr("shared.loading")}
          </p>
        ) : !isAdmin ? (
          <p
            className="text-sm text-muted-foreground"
            data-testid="viewer-read-only-notice"
          >
            {tr("admin.viewer.readOnlyNotice")}
          </p>
        ) : (
          <>
            <form
              noValidate
              onSubmit={(e) => void handleSubmit(e)}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="urls">{tr("admin.ingest.urlsLabel")}</Label>
                <Textarea
                  id="urls"
                  rows={5}
                  value={urlsText}
                  onChange={(e) => {
                    setUrlsText(e.target.value);
                  }}
                  placeholder={tr("admin.ingest.urlsPlaceholder")}
                  disabled={busy}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="chunk-size">
                  {tr("admin.ingest.chunkSizeLabel")}
                </Label>
                <Input
                  id="chunk-size"
                  type="number"
                  min={64}
                  value={chunkSize}
                  onChange={(e) => {
                    setChunkSize(e.target.value);
                  }}
                  disabled={busy}
                />
              </div>
              <div className="flex items-start gap-2">
                <input
                  id="ingest-crawl"
                  type="checkbox"
                  className="mt-1"
                  checked={crawl}
                  disabled={busy}
                  data-testid="ingest-crawl"
                  onChange={(e) => {
                    setCrawl(e.target.checked);
                  }}
                />
                <Label htmlFor="ingest-crawl" className="font-normal">
                  {tr("admin.ingest.crawlLabel")}
                </Label>
              </div>
              {crawl ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="ingest-max-depth">
                      {tr("admin.ingest.maxDepthLabel")}
                    </Label>
                    <Input
                      id="ingest-max-depth"
                      type="number"
                      min={0}
                      value={maxDepth}
                      data-testid="ingest-max-depth"
                      onChange={(e) => {
                        setMaxDepth(e.target.value);
                      }}
                      disabled={busy}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ingest-max-pages">
                      {tr("admin.ingest.maxPagesLabel")}
                    </Label>
                    <Input
                      id="ingest-max-pages"
                      type="number"
                      min={1}
                      value={maxPages}
                      data-testid="ingest-max-pages"
                      onChange={(e) => {
                        setMaxPages(e.target.value);
                      }}
                      disabled={busy}
                    />
                  </div>
                </div>
              ) : null}
              <Button type="submit" disabled={busy}>
                {busy ? tr("admin.ingest.running") : tr("admin.ingest.submit")}
              </Button>
            </form>
            {error ? (
              <p role="alert" className="mt-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
            {activeJob ? (
              <div
                className="mt-4 rounded-md bg-muted p-3"
                data-testid="job-status"
              >
                <p className="text-sm">
                  {tr("admin.ingest.jobStatusPrefix")}{" "}
                  <code className="font-mono text-xs">{activeJob.job_id}</code>:{" "}
                  <strong>{activeJob.status}</strong>
                </p>
                {activeJob.error_code ? (
                  <p className="mt-1 text-sm text-destructive">
                    {activeJob.error_code}: {activeJob.error_message}
                  </p>
                ) : null}
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
