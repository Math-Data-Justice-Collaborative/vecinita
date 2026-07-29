import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { type StringMessageKey } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

import {
  cancelJob,
  deleteJob,
  getJob,
  retryJob,
  subscribeJobEvents,
} from "@/api/jobs";
import type { Job, JobStatus, JobType } from "@/api/types";
import { useIsAdmin } from "@/auth/auth-context";
import { requireAdminConfig } from "@/config";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

const POLL_MS = 4000;
const SSE_RETRY_BASE_MS = 2000;
const SSE_RETRY_MAX_MS = 30000;

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

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

const TYPE_KEY: Record<JobType, StringMessageKey> = {
  ingest: "admin.jobs.type.ingest",
  retag: "admin.jobs.type.retag",
  eval: "admin.jobs.type.eval",
};

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const tr = useAdminT();
  const navigate = useNavigate();
  const { locale } = useLocale();
  const isAdmin = useIsAdmin();
  const trRef = useRef(tr);
  useEffect(() => {
    trRef.current = tr;
  }, [tr]);

  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(
    async (isActive: () => boolean) => {
      if (!jobId) return;
      try {
        const client = requireAdminConfig();
        const next = await getJob(client, jobId);
        if (!isActive()) return;
        setJob(next);
        setError(null);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error
            ? err.message
            : trRef.current("admin.jobs.loadFailed"),
        );
      }
    },
    [jobId],
  );

  useEffect(() => {
    let active = true;
    void load(() => active);
    return () => {
      active = false;
    };
  }, [load]);

  useEffect(() => {
    if (!jobId) return;
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
          onJob: (eventJob) => {
            if (!active || eventJob.job_id !== jobId) return;
            setJob(eventJob);
            stopPoll();
            retryAttempt = 0;
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
  }, [jobId, load]);

  const runAction = async (action: "cancel" | "retry" | "delete") => {
    if (!jobId || !job) return;
    setBusy(true);
    setActionError(null);
    try {
      const client = requireAdminConfig();
      if (action === "cancel") {
        setJob(await cancelJob(client, jobId));
      } else if (action === "retry") {
        const created = await retryJob(client, jobId);
        void navigate(`/jobs/${encodeURIComponent(created.job_id)}`);
      } else {
        await deleteJob(client, jobId);
        void navigate("/jobs");
      }
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : tr("admin.jobs.actionFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  if (error) {
    return (
      <div className="space-y-4">
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
        <Button variant="outline" asChild>
          <Link to="/jobs">{tr("admin.jobs.backToList")}</Link>
        </Button>
      </div>
    );
  }

  if (!job) {
    return <p className="text-muted-foreground">{tr("shared.loading")}</p>;
  }

  const jobType: JobType = job.job_type ?? "ingest";
  const canCancel =
    isAdmin && (job.status === "pending" || job.status === "running");
  const canRetry =
    isAdmin && (job.status === "failed" || job.status === "cancelled");
  const canDelete =
    isAdmin &&
    (job.status === "completed" ||
      job.status === "failed" ||
      job.status === "cancelled");

  return (
    <div className="space-y-6" data-testid="job-detail">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.jobs.detailTitle")}
          </h2>
          <p className="font-mono text-sm text-muted-foreground">{job.job_id}</p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/jobs">{tr("admin.jobs.backToList")}</Link>
        </Button>
      </div>

      {actionError ? (
        <p role="alert" className="text-sm text-destructive">
          {actionError}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>{tr(TYPE_KEY[jobType])}</span>
            <Badge variant={STATUS_VARIANT[job.status]}>
              {tr(STATUS_KEY[job.status])}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <span className="text-muted-foreground">
              {tr("admin.jobs.columnUpdated")}:{" "}
            </span>
            {formatLocaleDateTime(locale, job.updated_at)}
          </p>
          <p>
            <span className="text-muted-foreground">
              {tr("admin.jobs.createdAt")}:{" "}
            </span>
            {formatLocaleDateTime(locale, job.created_at)}
          </p>
          {jobType === "retag" && job.document_id ? (
            <p>
              <span className="text-muted-foreground">
                {tr("admin.jobs.documentId")}:{" "}
              </span>
              <code className="font-mono text-xs">{job.document_id}</code>
            </p>
          ) : null}
          {job.urls.length > 0 ? (
            <p>
              <span className="text-muted-foreground">
                {tr("admin.jobs.columnUrls")}:{" "}
              </span>
              {job.urls.join(", ")}
            </p>
          ) : null}
          {jobType === "eval" ? (
            <p>
              <Link
                className="text-primary underline"
                to={`/evaluation?run=${encodeURIComponent(job.eval_run_id ?? job.job_id)}&tab=runs`}
              >
                {tr("admin.jobs.openEvaluation")}
              </Link>
            </p>
          ) : null}
          {job.status === "failed" ? (
            <p className="text-destructive">
              {job.error_code
                ? `${job.error_code}: ${job.error_message ?? ""}`
                : (job.error_message ?? tr("shared.emDash"))}
            </p>
          ) : null}
          {job.modal_call_id ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-muted-foreground">
                {tr("admin.jobs.modalCallId")}:
              </span>
              <code className="font-mono text-xs">{job.modal_call_id}</code>
              <Button
                type="button"
                size="sm"
                variant="outline"
                aria-label={tr("admin.jobs.copyCallId")}
                onClick={() => {
                  void navigator.clipboard.writeText(job.modal_call_id);
                }}
              >
                {tr("admin.jobs.copyCallId")}
              </Button>
              {job.dashboard_url ? (
                <a
                  className="text-primary underline text-sm"
                  href={job.dashboard_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {tr("admin.jobs.modalDashboard")}
                </a>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {isAdmin ? (
        <div className="flex flex-wrap gap-2">
          {canCancel ? (
            <Button
              type="button"
              variant="secondary"
              disabled={busy}
              onClick={() => void runAction("cancel")}
            >
              {tr("admin.jobs.actionCancel")}
            </Button>
          ) : null}
          {canRetry ? (
            <Button
              type="button"
              variant="secondary"
              disabled={busy}
              onClick={() => void runAction("retry")}
            >
              {tr("admin.jobs.actionRetry")}
            </Button>
          ) : null}
          {canDelete ? (
            <Button
              type="button"
              variant="destructive"
              disabled={busy}
              onClick={() => void runAction("delete")}
            >
              {tr("admin.jobs.actionDelete")}
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
