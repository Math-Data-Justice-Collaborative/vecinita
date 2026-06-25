import { useCallback, useEffect, useState } from "react";
import { useLocale } from "vecinita-frontend-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { type StatsSummary, fetchStatsSummary } from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

export function DashboardPage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const data = await fetchStatsSummary(client);
      setStats(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.dashboard.loadFailed"),
      );
    } finally {
      setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.dashboard.title")}
          </h2>
          <p className="text-muted-foreground">
            {tr("admin.dashboard.subtitle")}
          </p>
        </div>
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.dashboard.title")}
          </h2>
        </div>
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {tr("admin.dashboard.title")}
        </h2>
        <p className="text-muted-foreground">
          {tr("admin.dashboard.subtitle")}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {tr("admin.dashboard.stats.totalDocuments")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_documents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {tr("admin.dashboard.stats.totalChunks")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_chunks}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {tr("admin.dashboard.stats.tags")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.tag_distribution.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {tr("admin.dashboard.stats.languages")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.language_breakdown.length}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.dashboard.topServed.title")}</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.top_served.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {tr("admin.dashboard.topServed.empty")}
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      {tr("admin.dashboard.topServed.columnDocument")}
                    </TableHead>
                    <TableHead className="text-right">
                      {tr("admin.dashboard.topServed.columnServed")}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.top_served.map((item) => (
                    <TableRow key={item.document_id}>
                      <TableCell>{item.title ?? item.document_id}</TableCell>
                      <TableCell className="text-right">
                        {item.served_count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.dashboard.recentActivity.title")}</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recent_activity.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {tr("admin.dashboard.recentActivity.empty")}
              </p>
            ) : (
              <div className="space-y-3">
                {stats.recent_activity.map((event, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Badge variant="outline">{event.event_type}</Badge>
                      <span className="text-muted-foreground truncate">
                        {event.summary ?? event.entity_type}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatLocaleDateTime(locale, event.timestamp)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
