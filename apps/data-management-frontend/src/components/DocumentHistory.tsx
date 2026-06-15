import { useCallback, useEffect, useState } from "react";
import { useLocale } from "vecinita-frontend-ui";

import { Badge } from "@/components/ui/badge";
import { type AuditEvent, fetchDocumentHistory } from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

interface DocumentHistoryProps {
  documentId: string;
}

export function DocumentHistory({ documentId }: DocumentHistoryProps) {
  const tr = useAdminT();
  const { locale } = useLocale();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const client = requireCorpusConfig();
      const data = await fetchDocumentHistory(client, documentId);
      setEvents(data);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <p className="text-sm text-muted-foreground">
        {tr("admin.documentHistory.loading")}
      </p>
    );
  }

  if (events.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {tr("admin.documentHistory.empty")}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">
        {tr("admin.documentHistory.title")}
      </h4>
      <div className="relative space-y-3 border-l-2 border-muted pl-4">
        {events.map((event) => (
          <div key={event.id} className="relative">
            <div className="absolute -left-[1.4rem] top-1 h-2.5 w-2.5 rounded-full bg-primary" />
            <div className="flex items-center gap-2 text-sm">
              <Badge variant="outline" className="text-xs">
                {event.event_type}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {formatLocaleDateTime(locale, event.timestamp)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
