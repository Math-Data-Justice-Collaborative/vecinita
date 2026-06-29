import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useLocale } from "vecinita-frontend-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type HealthAggregate, fetchHealthAggregate } from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";
import { cn } from "@/lib/utils";

export function HealthPage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [health, setHealth] = useState<HealthAggregate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isActive: () => boolean) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const data = await fetchHealthAggregate(client);
        if (!isActive()) return;
        setHealth(data);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error ? err.message : tr("admin.health.loadFailed"),
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

  if (loading && !health) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.health.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.health.subtitle")}</p>
        </div>
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.health.title")}
          </h2>
        </div>
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  /* v8 ignore next -- defensive: the health client throws on malformed payloads, so a falsy health with no error is unreachable */
  if (!health) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.health.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.health.subtitle")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            data-testid="overall-status"
            className={cn(
              health.overall === "healthy"
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
            )}
          >
            {health.overall}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load(() => true)}
            disabled={loading}
            aria-label={tr("admin.health.refreshAria")}
          >
            <RefreshCw
              className={cn("mr-2 h-4 w-4", loading && "animate-spin")}
            />
            {tr("shared.refresh")}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {health.services.map((service) => (
          <Card key={service.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {service.name}
              </CardTitle>
              <Badge
                variant={
                  service.status === "healthy" ? "default" : "destructive"
                }
              >
                {service.status}
              </Badge>
            </CardHeader>
            <CardContent>
              {service.latency_ms !== null ? (
                <p className="text-sm text-muted-foreground">
                  {tr("admin.health.latencyMs", { ms: service.latency_ms })}
                </p>
              ) : null}
              {service.error ? (
                <p className="text-sm text-destructive">{service.error}</p>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        {tr("admin.health.lastChecked", {
          datetime: formatLocaleDateTime(locale, health.checked_at),
        })}
      </p>
    </div>
  );
}
