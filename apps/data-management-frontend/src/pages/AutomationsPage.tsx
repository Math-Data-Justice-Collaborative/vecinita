/**
 * F75 Automations panel — enable/disable + run history (UJ-080).
 * [Corpus: feature-list.md §F75]
 * [Corpus: user-journeys.md §UJ-080]
 * [Spec: docs/acceptance-criteria.md §AC-AU1, AC-AU5]
 */
import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ActionIcon, useLocale } from "vecinita-frontend-ui";

import {
  fetchAutomationRuns,
  fetchAutomationsConfig,
  patchAutomationsEnabled,
  type AutomationRun,
  type AutomationsConfig,
} from "@/api/automations";
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
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";
import { TruncatedText } from "@/components/TruncatedText";

export function AutomationsPage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [config, setConfig] = useState<AutomationsConfig | null>(null);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isActive: () => boolean) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const [cfg, runList] = await Promise.all([
          fetchAutomationsConfig(client),
          fetchAutomationRuns(client),
        ]);
        if (!isActive()) return;
        setConfig(cfg);
        setRuns(runList.items);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error
            ? err.message
            : tr("admin.automations.loadFailed"),
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

  const onToggleEnabled = async (nextEnabled: boolean) => {
    setToggling(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const updated = await patchAutomationsEnabled(client, nextEnabled);
      setConfig(updated);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.automations.toggleFailed"),
      );
    } finally {
      setToggling(false);
    }
  };

  const emDash = tr("shared.emDash");

  return (
    <div className="space-y-6" data-testid="automations-admin-page">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.automations.title")}
          </h2>
          <p className="text-muted-foreground">
            {tr("admin.automations.subtitle")}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void load(() => true)}
          disabled={loading || toggling}
          aria-label={tr("admin.automations.refreshAria")}
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

      {loading && !config ? (
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      ) : null}

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {config ? (
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.automations.configTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <input
                  id="automations-enabled"
                  type="checkbox"
                  className="h-4 w-4"
                  checked={config.enabled}
                  disabled={toggling}
                  data-testid="automations-enabled-toggle"
                  aria-label={tr("admin.automations.enabledLabel")}
                  onChange={(e) => {
                    void onToggleEnabled(e.target.checked);
                  }}
                />
                <Label htmlFor="automations-enabled" className="font-normal">
                  {tr("admin.automations.enabledLabel")}
                </Label>
              </div>
              <Badge
                data-testid="automations-enabled-status"
                variant={config.enabled ? "default" : "secondary"}
              >
                {config.enabled
                  ? tr("admin.automations.status.enabled")
                  : tr("admin.automations.status.disabled")}
              </Badge>
            </div>

            <div className="grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <span className="text-muted-foreground">
                  {tr("admin.automations.killSwitchLabel")}:{" "}
                </span>
                <span data-testid="automations-kill-switch">
                  {config.kill_switch
                    ? tr("admin.automations.killSwitch.on")
                    : tr("admin.automations.killSwitch.off")}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">
                  {tr("admin.automations.maxConcurrentLabel")}:{" "}
                </span>
                <span data-testid="automations-max-concurrent">
                  {String(config.max_concurrent)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {config ? (
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.automations.runsTitle")}</CardTitle>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <p data-testid="automations-runs-empty">
                {tr("admin.automations.runsEmpty")}
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      {tr("admin.automations.table.jobType")}
                    </TableHead>
                    <TableHead>
                      {tr("admin.automations.table.status")}
                    </TableHead>
                    <TableHead>
                      {tr("admin.automations.table.started")}
                    </TableHead>
                    <TableHead>
                      {tr("admin.automations.table.finished")}
                    </TableHead>
                    <TableHead>{tr("admin.automations.table.error")}</TableHead>
                    <TableHead>
                      {tr("admin.automations.table.document")}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id} data-testid="automation-run-row">
                      <TableCell>{run.job_type}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            run.status === "failed"
                              ? "destructive"
                              : run.status === "completed"
                                ? "default"
                                : "secondary"
                          }
                        >
                          {run.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {run.started_at
                          ? formatLocaleDateTime(locale, run.started_at)
                          : emDash}
                      </TableCell>
                      <TableCell>
                        {run.finished_at
                          ? formatLocaleDateTime(locale, run.finished_at)
                          : emDash}
                      </TableCell>
                      <TableCell className="max-w-[12rem]">
                        {run.error ? (
                          <TruncatedText text={run.error} />
                        ) : (
                          emDash
                        )}
                      </TableCell>
                      <TableCell className="max-w-[8rem]">
                        {run.document_id ? (
                          <TruncatedText text={run.document_id} />
                        ) : (
                          emDash
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
