/**
 * F77 Fine-tune panel — approve train, eval evidence, human promote (UJ-082).
 * [Corpus: feature-list.md §F77]
 * [Corpus: user-journeys.md §UJ-082]
 * [Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT3 §AC-FT4 §AC-FT9]
 * [Spec: docs/test-plan.md §TC-260 §TC-261 §TC-262 §TC-265]
 */
import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ActionIcon, useLocale } from "vecinita-frontend-ui";

import {
  approveFinetuneJob,
  createFinetuneTrainJob,
  fetchFinetuneAdapterPin,
  fetchFinetuneEval,
  listFinetuneJobs,
  promoteFinetuneAdapter,
  rollbackFinetuneAdapter,
  type FinetuneAdapterPin,
  type FinetuneEvalReport,
} from "@/api/finetune";
import type { Job } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TruncatedText } from "@/components/TruncatedText";
import { requireAdminConfig, requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

function metricText(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return String(value);
}

export function FinetunePage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [pin, setPin] = useState<FinetuneAdapterPin | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evalReport, setEvalReport] = useState<FinetuneEvalReport | null>(null);
  const [promoteConfirm, setPromoteConfirm] = useState(false);

  const load = useCallback(
    async (isActive: () => boolean) => {
      setLoading(true);
      setError(null);
      try {
        const admin = requireAdminConfig();
        const corpus = requireCorpusConfig();
        const [nextPin, nextJobs] = await Promise.all([
          fetchFinetuneAdapterPin(corpus),
          listFinetuneJobs(admin),
        ]);
        if (!isActive()) return;
        setPin(nextPin);
        setJobs(nextJobs);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error ? err.message : tr("admin.finetune.loadFailed"),
        );
      } finally {
        if (isActive()) setLoading(false);
      }
    },
    [tr],
  );

  useEffect(() => {
    let active = true;
    void load(() => active);
    return () => {
      active = false;
    };
  }, [load]);

  const onRequestTrain = async () => {
    setBusy(true);
    setError(null);
    try {
      await createFinetuneTrainJob(requireAdminConfig());
      await load(() => true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.finetune.requestFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const onApprove = async (jobId: string) => {
    setBusy(true);
    setError(null);
    try {
      await approveFinetuneJob(requireAdminConfig(), jobId);
      await load(() => true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.finetune.approveFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const onViewEval = async (jobId: string) => {
    setBusy(true);
    setError(null);
    setPromoteConfirm(false);
    try {
      const report = await fetchFinetuneEval(requireCorpusConfig(), jobId);
      setEvalReport(report);
    } catch (err) {
      setEvalReport(null);
      setError(
        err instanceof Error ? err.message : tr("admin.finetune.evalFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const onPromote = async () => {
    if (!evalReport || !promoteConfirm) return;
    setBusy(true);
    setError(null);
    try {
      const result = await promoteFinetuneAdapter(
        requireCorpusConfig(),
        evalReport.adapter_id,
      );
      setPin({
        adapter_id: result.adapter_id,
        base: result.base,
      });
      setPromoteConfirm(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.finetune.promoteFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const onRollback = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await rollbackFinetuneAdapter(requireCorpusConfig());
      setPin({
        adapter_id: result.adapter_id,
        base: result.base,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.finetune.rollbackFailed"),
      );
    } finally {
      setBusy(false);
    }
  };

  const emDash = tr("shared.emDash");

  return (
    <div className="space-y-6" data-testid="finetune-admin-page">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.finetune.title")}
          </h2>
          <p className="text-muted-foreground">
            {tr("admin.finetune.subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={() => void onRequestTrain()}
            disabled={loading || busy}
            data-testid="finetune-request-train-btn"
          >
            {tr("admin.finetune.requestTrain")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load(() => true)}
            disabled={loading || busy}
            aria-label={tr("admin.finetune.refreshAria")}
          >
            <ActionIcon
              motion="spin"
              pending={loading}
              className="mr-2 inline-flex"
            >
              <RefreshCw className="h-4 w-4" />
            </ActionIcon>
            {tr("shared.refresh")}
          </Button>
        </div>
      </div>

      {loading && !pin ? (
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      ) : null}

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {pin ? (
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.finetune.prodPinTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-4">
            <div>
              <span className="text-muted-foreground">
                {tr("admin.finetune.prodPinLabel")}:{" "}
              </span>
              <span data-testid="finetune-prod-pin">
                {pin.base || !pin.adapter_id
                  ? tr("admin.finetune.prodPin.base")
                  : pin.adapter_id}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void onRollback()}
              disabled={busy || pin.base || !pin.adapter_id}
              data-testid="finetune-rollback-btn"
            >
              {tr("admin.finetune.rollback")}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {pin ? (
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.finetune.jobsTitle")}</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <p data-testid="finetune-jobs-empty">
                {tr("admin.finetune.jobsEmpty")}
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{tr("admin.finetune.table.jobId")}</TableHead>
                    <TableHead>{tr("admin.finetune.table.status")}</TableHead>
                    <TableHead>{tr("admin.finetune.table.approved")}</TableHead>
                    <TableHead>{tr("admin.finetune.table.adapter")}</TableHead>
                    <TableHead>{tr("admin.finetune.table.updated")}</TableHead>
                    <TableHead>{tr("admin.finetune.table.actions")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => {
                    const adapterId = job.metrics?.adapter_id ?? null;
                    const needsApprove =
                      job.status === "pending" && job.approved === false;
                    const canViewEval =
                      job.status === "completed" || adapterId !== null;
                    return (
                      <TableRow key={job.job_id} data-testid="finetune-job-row">
                        <TableCell className="max-w-[10rem]">
                          <TruncatedText text={job.job_id} />
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              job.status === "failed"
                                ? "destructive"
                                : job.status === "completed"
                                  ? "default"
                                  : "secondary"
                            }
                          >
                            {job.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {job.approved === true
                            ? tr("admin.finetune.approved.yes")
                            : job.approved === false
                              ? tr("admin.finetune.approved.no")
                              : emDash}
                        </TableCell>
                        <TableCell className="max-w-[10rem]">
                          {adapterId ? (
                            <TruncatedText text={adapterId} />
                          ) : (
                            emDash
                          )}
                        </TableCell>
                        <TableCell>
                          {formatLocaleDateTime(locale, job.updated_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            {needsApprove ? (
                              <Button
                                size="sm"
                                onClick={() => void onApprove(job.job_id)}
                                disabled={busy}
                                data-testid="finetune-approve-btn"
                              >
                                {tr("admin.finetune.approve")}
                              </Button>
                            ) : null}
                            {canViewEval ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => void onViewEval(job.job_id)}
                                disabled={busy}
                                data-testid="finetune-view-eval-btn"
                              >
                                {tr("admin.finetune.viewEval")}
                              </Button>
                            ) : null}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : null}

      {evalReport ? (
        <Card data-testid="finetune-eval-report">
          <CardHeader>
            <CardTitle>{tr("admin.finetune.evalTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p
              className="text-sm text-muted-foreground"
              data-testid="finetune-eval-summary"
            >
              {evalReport.summary}
            </p>
            <div className="flex flex-wrap gap-3 text-sm">
              <span>
                {tr("admin.finetune.eval.adapter")}:{" "}
                <TruncatedText text={evalReport.adapter_id} />
              </span>
              <span>
                {tr("admin.finetune.eval.baseModel")}:{" "}
                {evalReport.base_model_id}
              </span>
              <Badge variant="secondary" data-testid="finetune-auto-promote">
                {tr("admin.finetune.autoPromote")}:{" "}
                {evalReport.auto_promote
                  ? tr("admin.finetune.autoPromote.on")
                  : tr("admin.finetune.autoPromote.off")}
              </Badge>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1 text-sm">
                <p className="font-medium">{tr("admin.finetune.eval.base")}</p>
                <p>
                  {tr("admin.finetune.eval.faithfulness")}:{" "}
                  <span data-testid="finetune-eval-base-faithfulness">
                    {metricText(evalReport.base.faithfulness)}
                  </span>
                </p>
                <p>
                  {tr("admin.finetune.eval.answerRelevancy")}:{" "}
                  {metricText(evalReport.base.answer_relevancy)}
                </p>
                <p>
                  {tr("admin.finetune.eval.questionsScored")}:{" "}
                  {String(evalReport.base.questions_scored)}
                </p>
              </div>
              <div className="space-y-1 text-sm">
                <p className="font-medium">
                  {tr("admin.finetune.eval.adapterSide")}
                </p>
                <p>
                  {tr("admin.finetune.eval.faithfulness")}:{" "}
                  <span data-testid="finetune-eval-adapter-faithfulness">
                    {metricText(evalReport.adapter.faithfulness)}
                  </span>
                </p>
                <p>
                  {tr("admin.finetune.eval.answerRelevancy")}:{" "}
                  {metricText(evalReport.adapter.answer_relevancy)}
                </p>
                <p>
                  {tr("admin.finetune.eval.questionsScored")}:{" "}
                  {String(evalReport.adapter.questions_scored)}
                </p>
              </div>
            </div>
            <div className="space-y-3 border-t pt-4">
              <div className="flex items-center gap-2">
                <input
                  id="finetune-promote-confirm"
                  type="checkbox"
                  className="h-4 w-4"
                  checked={promoteConfirm}
                  disabled={busy}
                  data-testid="finetune-promote-confirm"
                  aria-label={tr("admin.finetune.promoteConfirmLabel")}
                  onChange={(e) => {
                    setPromoteConfirm(e.target.checked);
                  }}
                />
                <Label
                  htmlFor="finetune-promote-confirm"
                  className="font-normal"
                >
                  {tr("admin.finetune.promoteConfirmLabel")}
                </Label>
              </div>
              <Button
                onClick={() => void onPromote()}
                disabled={busy || !promoteConfirm}
                data-testid="finetune-promote-btn"
              >
                {tr("admin.finetune.promote")}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
