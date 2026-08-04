import { useCallback, useEffect, useState } from "react";
import { useLocale } from "vecinita-frontend-ui";

import {
  fetchFeedbackList,
  type FeedbackItem,
  type FeedbackListResponse,
} from "@/api/feedback";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { requireAdminConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

export function FeedbackPage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [data, setData] = useState<FeedbackListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isActive: () => boolean) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireAdminConfig();
        const result = await fetchFeedbackList(client);
        if (!isActive()) return;
        setData(result);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error ? err.message : tr("admin.feedback.loadFailed"),
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

  return (
    <div className="space-y-4" data-testid="feedback-admin-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {tr("admin.feedback.title")}
        </h1>
        <p className="text-muted-foreground">{tr("admin.feedback.subtitle")}</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.feedback.tableTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <p>{tr("shared.loading")}</p> : null}
          {error ? (
            <p className="text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          {!loading && !error && data ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{tr("admin.feedback.table.created")}</TableHead>
                  <TableHead>{tr("admin.feedback.table.category")}</TableHead>
                  <TableHead>{tr("admin.feedback.table.message")}</TableHead>
                  <TableHead>{tr("admin.feedback.table.locale")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4}>
                      {tr("admin.feedback.empty")}
                    </TableCell>
                  </TableRow>
                ) : (
                  data.items.map((item: FeedbackItem) => (
                    <TableRow key={item.id} data-testid="feedback-row">
                      <TableCell>
                        {formatLocaleDateTime(locale, item.created_at)}
                      </TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell className="max-w-xl whitespace-pre-wrap">
                        {item.message}
                      </TableCell>
                      <TableCell>{item.locale ?? "—"}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
