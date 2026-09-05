import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { type StringMessageKey } from "vecinita-frontend-i18n";
import { ActionIcon, useLocale } from "vecinita-frontend-ui";
import { useNavigate } from "react-router-dom";

import { listJobs, subscribeJobEvents } from "@/api/jobs";
import type { Job, JobStatus, JobType } from "@/api/types";
import { requireAdminConfig } from "@/config";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";
import { TruncatedText } from "@/components/TruncatedText";

const POLL_MS = 4000;
const SSE_RETRY_BASE_MS = 2000;
const SSE_RETRY_MAX_MS = 30000;

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";
type StatusFilter = JobStatus | "all";

const STATUS_VARIANT: Record<JobStatus, BadgeVariant> = {
  pending: "outline",
  running: "secondary",
  completed: "default",
  failed: "destructive",
  cancelled: "outline",
};

const STATUS_KEY: Record<JobStatus, StringMessageKey> = {
  pending: "admin.jobs.status.pending",
  running: "admin.jobs.status.running",
  completed: "admin.jobs.status.completed",
  failed: "admin.jobs.status.failed",
  cancelled: "admin.jobs.status.cancelled",
};

const TYPE_KEY: Partial<Record<JobType, StringMessageKey>> = {
  ingest: "admin.jobs.type.ingest",
  retag: "admin.jobs.type.retag",
  eval: "admin.jobs.type.eval",
  rebuild: "admin.jobs.type.rebuild",
  finetune_train: "admin.jobs.type.finetune_train",
};

function contextCell(job: Job, emDash: string): string {
  if (job.job_type === "retag" && job.document_id) {
    return job.document_id;
  }
  if (job.urls.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- length guard
    const first = job.urls[0]!;
    return job.urls.length > 1
      ? `${first} (+${String(job.urls.length - 1)})`
      : first;
  }
  return emDash;
}

export function JobsPage() {
  const tr = useAdminT();
  const navigate = useNavigate();
  const trRef = useRef(tr);
  useEffect(() => {
    trRef.current = tr;
  }, [tr]);
  const { locale } = useLocale();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sseFailed, setSseFailed] = useState(false);
  const statusFilterRef = useRef(statusFilter);
  useEffect(() => {
    statusFilterRef.current = statusFilter;
  }, [statusFilter]);

  const load = useCallback(async (isActive: () => boolean = () => true) => {
    if (isActive()) setLoading(true);
    try {
      const client = requireAdminConfig();
      const filter = statusFilterRef.current;
      const list = await listJobs(
        client,
        filter === "all" ? undefined : filter,
      );
      if (!isActive()) return;
      setJobs(list);
      setError(null);
    } catch (err) {
      if (!isActive()) return;
      setError(
        err instanceof Error
          ? err.message
          : trRef.current("admin.jobs.loadFailed"),
      );
    } finally {
      if (isActive()) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const isActive = () => active;
    void load(isActive);
    return () => {
      active = false;
    };
  }, [load, statusFilter]);

  useEffect(() => {
    let active = true;
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let subscription: { close: () => void } | null = null;
    let retryAttempt = 0;

    const stopPoll = () => {
      if (pollTimer !== null) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    };

    const startPoll = () => {
      if (pollTimer !== null) return;
      setSseFailed(true);
      void load(() => active);
      pollTimer = setInterval(() => {
        void load(() => active);
      }, POLL_MS);
    };

    const connectSse = () => {
      if (!active) return;
      try {
        const client = requireAdminConfig();
        subscription = subscribeJobEvents(client, {
          onJob: (job) => {
            if (!active) return;
            setSseFailed(false);
            stopPoll();
            retryAttempt = 0;
            setJobs((prev) => {
              const filter = statusFilterRef.current;
              if (filter !== "all" && job.status !== filter) {
                return prev.filter((j) => j.job_id !== job.job_id);
              }
              const idx = prev.findIndex((j) => j.job_id === job.job_id);
              if (idx === -1) {
                return [job, ...prev];
              }
              const next = [...prev];
              next[idx] = job;
              return next;
            });
            setError(null);
          },
          onError: () => {
            if (!active) return;
            subscription?.close();
            subscription = null;
            startPoll();
            const delay = Math.min(
              SSE_RETRY_BASE_MS * 2 ** retryAttempt,
              SSE_RETRY_MAX_MS,
            );
            retryAttempt += 1;
            retryTimer = setTimeout(() => {
              if (active) connectSse();
            }, delay);
          },
        });
      } catch {
        startPoll();
      }
    };

    connectSse();

    return () => {
      active = false;
      stopPoll();
      if (retryTimer !== null) clearTimeout(retryTimer);
      subscription?.close();
    };
  }, [load]);

  return (
    <div className="space-y-6" data-testid="jobs-page">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.jobs.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.jobs.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">
              {tr("admin.jobs.columnStatus")}
            </span>
            <select
              aria-label={tr("admin.jobs.columnStatus")}
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as StatusFilter);
                setLoading(true);
              }}
            >
              <option value="all">{tr("admin.jobs.filterAll")}</option>
              <option value="pending">{tr("admin.jobs.status.pending")}</option>
              <option value="running">{tr("admin.jobs.status.running")}</option>
              <option value="completed">
                {tr("admin.jobs.status.completed")}
              </option>
              <option value="failed">{tr("admin.jobs.status.failed")}</option>
              <option value="cancelled">
                {tr("admin.jobs.status.cancelled")}
              </option>
            </select>
          </label>
          <Button
            variant="outline"
            size="icon"
            aria-label={tr("shared.refresh")}
            onClick={() => void load()}
            disabled={loading}
            data-testid="jobs-refresh"
          >
            <ActionIcon
              motion="spin"
              pending={loading}
              data-testid="jobs-refresh-icon"
            >
              <RefreshCw className="h-4 w-4" />
            </ActionIcon>
          </Button>
        </div>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
      {sseFailed ? (
        <p
          className="text-xs text-muted-foreground"
          data-testid="jobs-poll-fallback"
        >
          {tr("admin.jobs.pollFallback")}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.jobs.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && jobs.length === 0 ? (
            <p className="text-muted-foreground">{tr("shared.loading")}</p>
          ) : jobs.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {tr("admin.jobs.empty")}
            </p>
          ) : (
            <Table className="table-fixed">
              <TableHeader>
                <TableRow>
                  <TableHead>{tr("admin.jobs.columnJob")}</TableHead>
                  <TableHead>{tr("admin.jobs.columnType")}</TableHead>
                  <TableHead>{tr("admin.jobs.columnStatus")}</TableHead>
                  <TableHead>{tr("admin.jobs.columnUrls")}</TableHead>
                  <TableHead>{tr("admin.jobs.columnUpdated")}</TableHead>
                  <TableHead>{tr("admin.jobs.columnError")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => {
                  const jobType: JobType = job.job_type ?? "ingest";
                  const typeKey = TYPE_KEY[jobType];
                  return (
                    <TableRow
                      key={job.job_id}
                      data-testid="job-row"
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => {
                        void navigate(
                          `/jobs/${encodeURIComponent(job.job_id)}`,
                        );
                      }}
                    >
                      <TableCell>
                        <code className="font-mono text-xs" title={job.job_id}>
                          {job.job_id.slice(0, 8)}
                        </code>
                      </TableCell>
                      <TableCell>{typeKey ? tr(typeKey) : jobType}</TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[job.status]}>
                          {tr(STATUS_KEY[job.status])}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-0">
                        <TruncatedText
                          text={contextCell(job, tr("shared.emDash"))}
                          data-testid={`job-context-${job.job_id}`}
                        />
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatLocaleDateTime(locale, job.updated_at)}
                      </TableCell>
                      <TableCell className="max-w-0 text-xs text-destructive">
                        {job.status === "failed" && job.error_code ? (
                          <TruncatedText
                            text={`${job.error_code}: ${job.error_message ?? ""}`}
                            className="text-destructive"
                          />
                        ) : (
                          tr("shared.emDash")
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
