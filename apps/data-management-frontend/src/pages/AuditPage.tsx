import { useCallback, useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  type AuditEvent,
  type AuditPage as AuditPageData,
  fetchAuditLog,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { ChevronDown, ChevronRight } from "lucide-react";

export function AuditPage() {
  const [data, setData] = useState<AuditPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [entityIdFilter, setEntityIdFilter] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const load = useCallback(
    async (params?: { event_type?: string; entity_id?: string }) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const result = await fetchAuditLog(client, params);
        setData(result);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load audit log",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const handleApplyFilters = () => {
    const params: { event_type?: string; entity_id?: string } = {};
    if (eventTypeFilter.trim()) params.event_type = eventTypeFilter.trim();
    if (entityIdFilter.trim()) params.entity_id = entityIdFilter.trim();
    void load(params);
  };

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Audit Log</h2>
          <p className="text-muted-foreground">
            Event history and document changes.
          </p>
        </div>
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Audit Log</h2>
        </div>
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Audit Log</h2>
        <p className="text-muted-foreground">
          Event history and document changes.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <label
                className="text-sm font-medium"
                htmlFor="filter-event-type"
              >
                Event type
              </label>
              <Input
                id="filter-event-type"
                data-testid="filter-event-type"
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                }}
                placeholder="document.created"
                className="w-48"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="filter-entity-id">
                Entity ID
              </label>
              <Input
                id="filter-entity-id"
                data-testid="filter-entity-id"
                value={entityIdFilter}
                onChange={(e) => {
                  setEntityIdFilter(e.target.value);
                }}
                placeholder="doc-aaa..."
                className="w-48"
              />
            </div>
            <Button
              size="sm"
              onClick={handleApplyFilters}
              data-testid="apply-filters"
            >
              Apply
            </Button>
          </div>
        </CardContent>
      </Card>

      {data && (
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8" />
                  <TableHead>Event Type</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Entity ID</TableHead>
                  <TableHead>Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.events.map((event) => (
                  <AuditRow
                    key={event.id}
                    event={event}
                    expanded={expandedIds.has(event.id)}
                    onToggle={() => {
                      toggleExpand(event.id);
                    }}
                  />
                ))}
              </TableBody>
            </Table>
            {data.events.length === 0 && (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No audit events found.
              </p>
            )}
            <p className="mt-3 text-xs text-muted-foreground">
              Showing {data.events.length} of {data.total} events
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function AuditRow({
  event,
  expanded,
  onToggle,
}: {
  event: AuditEvent;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <TableRow>
        <TableCell>
          <button
            type="button"
            onClick={onToggle}
            data-testid="expand-payload"
            className="rounded p-1 hover:bg-muted"
            aria-label={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </TableCell>
        <TableCell>
          <Badge variant="outline">{event.event_type}</Badge>
        </TableCell>
        <TableCell>{event.entity_type}</TableCell>
        <TableCell className="font-mono text-xs">{event.entity_id}</TableCell>
        <TableCell className="text-xs text-muted-foreground">
          {new Date(event.timestamp).toLocaleString()}
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow>
          <TableCell colSpan={5}>
            <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
