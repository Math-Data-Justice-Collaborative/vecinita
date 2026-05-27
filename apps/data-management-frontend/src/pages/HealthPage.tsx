import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { type HealthAggregate, fetchHealthAggregate } from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { cn } from "@/lib/utils";

export function HealthPage() {
  const [health, setHealth] = useState<HealthAggregate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const data = await fetchHealthAggregate(client);
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load health");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !health) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Health</h2>
          <p className="text-muted-foreground">Service status and connectivity.</p>
        </div>
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Health</h2>
        </div>
        <p role="alert" className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (!health) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Health</h2>
          <p className="text-muted-foreground">Service status and connectivity.</p>
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
          <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading} aria-label="Refresh">
            <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {health.services.map((service) => (
          <Card key={service.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{service.name}</CardTitle>
              <Badge
                variant={service.status === "healthy" ? "default" : "destructive"}
              >
                {service.status}
              </Badge>
            </CardHeader>
            <CardContent>
              {service.latency_ms !== null ? (
                <p className="text-sm text-muted-foreground">{service.latency_ms} ms</p>
              ) : null}
              {service.error ? (
                <p className="text-sm text-destructive">{service.error}</p>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        Last checked: {new Date(health.checked_at).toLocaleString()}
      </p>
    </div>
  );
}
