import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { type StringMessageKey } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";
import { useNavigate } from "react-router-dom";

import { listJobs } from "@/api/jobs";
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

const POLL_MS = 4000;

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

const STATUS_VARIANT: Record<JobStatus, BadgeVariant> = {
  pending: "outline",
  running: "secondary",
  completed: "default",
  failed: "destructive",
};

const STATUS_KEY: Record<JobStatus, StringMessageKey> = {
  pending: "admin.jobs.status.pending",
  running: "admin.jobs.status.running",
  completed: "admin.jobs.status.completed",
  failed: "admin.jobs.status.failed",
};

const TYPE_KEY: Record<JobType, StringMessageKey> = {
  ingest: "admin.jobs.type.ingest",
  retag: "admin.jobs.type.retag",
  eval: "admin.jobs.type.eval",
};

export function JobsPage() {
  const tr = useAdminT();
  const navigate = useNavigate();
  // Decouple the load path from `tr` (its identity changes on EN/ES switch) so a
  // locale toggle does not refire polling — same lesson as BUG-2026-06-25.
  const trRef = useRef(tr);
  useEffect(() => {
    trRef.current = tr;
  }, [tr]);
  const { locale } = useLocale();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (isActive: () => boolean = () => true) => {
    try {
      const client = requireAdminConfig();
      const list = await listJobs(client);
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
    const interval = setInterval(() => {
      void load(isActive);
    }, POLL_MS);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.jobs.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.jobs.subtitle")}</p>
        </div>
        <Button
          variant="outline"
          size="icon"
          aria-label={tr("shared.refresh")}
          onClick={() => void load()}
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
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
            <Table>
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
                  const isEval = jobType === "eval";
                  return (
                    <TableRow
                      key={job.job_id}
                      data-testid="job-row"
                      className={
                        isEval ? "cursor-pointer hover:bg-muted/50" : undefined
                      }
                      onClick={() => {
                        if (isEval) {
                          void navigate(
                            `/evaluation?run=${encodeURIComponent(job.job_id)}&tab=runs`,
                          );
                        }
                      }}
                    >
                      <TableCell>
                        <code className="font-mono text-xs" title={job.job_id}>
                          {job.job_id.slice(0, 8)}
                        </code>
                      </TableCell>
                      <TableCell>{tr(TYPE_KEY[jobType])}</TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANT[job.status]}>
                          {tr(STATUS_KEY[job.status])}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {job.urls.length > 0
                          ? job.urls[0]
                          : tr("shared.emDash")}
                        {job.urls.length > 1
                          ? ` (+${String(job.urls.length - 1)})`
                          : ""}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {formatLocaleDateTime(locale, job.updated_at)}
                      </TableCell>
                      <TableCell className="text-xs text-destructive">
                        {job.status === "failed" && job.error_code
                          ? `${job.error_code}: ${job.error_message ?? ""}`
                          : tr("shared.emDash")}
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
