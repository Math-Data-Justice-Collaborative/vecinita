import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { type StringMessageKey } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { useAdminT } from "@/hooks/useAdminT";
import { auditEventLabelKey } from "@/lib/auditEventLabel";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";
import { ChevronDown, ChevronRight } from "lucide-react";

type EntityTypeFilter = "all" | "user" | "document" | "email";

const ENTITY_TYPE_FILTER_KEY: Record<
  Exclude<EntityTypeFilter, "all">,
  StringMessageKey
> = {
  user: "admin.audit.filters.entityTypeUsers",
  document: "admin.audit.filters.entityTypeDocuments",
  email: "admin.audit.filters.entityTypeEmail",
};

export function AuditPage() {
  const tr = useAdminT();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<AuditPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [entityIdFilter, setEntityIdFilter] = useState(
    () => searchParams.get("entity_id") ?? "",
  );
  const [actorIdFilter, setActorIdFilter] = useState(
    () => searchParams.get("actor_id") ?? "",
  );
  const [entityTypeFilter, setEntityTypeFilter] =
    useState<EntityTypeFilter>("all");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const load = useCallback(
    async (
      params?: {
        event_type?: string;
        entity_id?: string;
        entity_type?: string;
        actor_id?: string;
      },
      isActive: () => boolean = () => true,
    ) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const result = await fetchAuditLog(client, params);
        if (!isActive()) return;
        setData(result);
      } catch (err) {
        if (!isActive()) return;
        setError(
          err instanceof Error ? err.message : tr("admin.audit.loadFailed"),
        );
      } finally {
        if (isActive()) setLoading(false);
      }
    },
    [tr],
  );

  useEffect(() => {
    let active = true;
    const entityId = searchParams.get("entity_id");
    const actorId = searchParams.get("actor_id");
    if (entityId) {
      setEntityIdFilter(entityId);
      void load({ entity_id: entityId }, () => active);
    } else if (actorId) {
      setActorIdFilter(actorId);
      void load({ actor_id: actorId }, () => active);
    } else {
      void load(undefined, () => active);
    }
    return () => {
      active = false;
    };
  }, [load, searchParams]);

  const handleApplyFilters = () => {
    const params: {
      event_type?: string;
      entity_id?: string;
      entity_type?: string;
      actor_id?: string;
    } = {};
    if (eventTypeFilter.trim()) params.event_type = eventTypeFilter.trim();
    if (entityIdFilter.trim()) params.entity_id = entityIdFilter.trim();
    if (actorIdFilter.trim()) params.actor_id = actorIdFilter.trim();
    if (entityTypeFilter !== "all") params.entity_type = entityTypeFilter;
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
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.audit.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.audit.subtitle")}</p>
        </div>
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.audit.title")}
          </h2>
        </div>
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="audit-page">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {tr("admin.audit.title")}
        </h2>
        <p className="text-muted-foreground">{tr("admin.audit.subtitle")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {tr("admin.audit.filters.title")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <label
                className="text-sm font-medium"
                htmlFor="filter-entity-type"
              >
                {tr("admin.audit.filters.entityTypeLabel")}
              </label>
              <Select
                value={entityTypeFilter}
                onValueChange={(value: string) => {
                  setEntityTypeFilter(value as EntityTypeFilter);
                }}
              >
                <SelectTrigger
                  id="filter-entity-type"
                  data-testid="filter-entity-type"
                  className="w-48"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">
                    {tr("admin.audit.filters.entityTypeAll")}
                  </SelectItem>
                  <SelectItem value="user">
                    {tr("admin.audit.filters.entityTypeUsers")}
                  </SelectItem>
                  <SelectItem value="document">
                    {tr("admin.audit.filters.entityTypeDocuments")}
                  </SelectItem>
                  <SelectItem value="email">
                    {tr("admin.audit.filters.entityTypeEmail")}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <label
                className="text-sm font-medium"
                htmlFor="filter-event-type"
              >
                {tr("admin.audit.filters.eventTypeLabel")}
              </label>
              <Input
                id="filter-event-type"
                data-testid="filter-event-type"
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                }}
                placeholder={tr("admin.audit.filters.eventTypePlaceholder")}
                className="w-48"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="filter-entity-id">
                {tr("admin.audit.filters.entityIdLabel")}
              </label>
              <Input
                id="filter-entity-id"
                data-testid="filter-entity-id"
                value={entityIdFilter}
                onChange={(e) => {
                  setEntityIdFilter(e.target.value);
                }}
                placeholder={tr("admin.audit.filters.entityIdPlaceholder")}
                className="w-48"
              />
            </div>
            <Button
              size="sm"
              onClick={handleApplyFilters}
              data-testid="apply-filters"
            >
              {tr("admin.audit.filters.apply")}
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
                  <TableHead>{tr("admin.audit.table.eventType")}</TableHead>
                  <TableHead>{tr("admin.audit.table.entity")}</TableHead>
                  <TableHead>{tr("admin.audit.table.entityId")}</TableHead>
                  <TableHead>{tr("admin.audit.table.timestamp")}</TableHead>
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
                {tr("admin.audit.empty")}
              </p>
            )}
            <p className="mt-3 text-xs text-muted-foreground">
              {tr("admin.audit.showingCount", {
                shown: data.events.length,
                total: data.total,
              })}
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
  const tr = useAdminT();
  const { locale } = useLocale();
  const labelKey = auditEventLabelKey(event.event_type);
  const eventLabel = labelKey ? tr(labelKey) : event.event_type;
  const entityLabel =
    event.entity_type in ENTITY_TYPE_FILTER_KEY
      ? tr(
          ENTITY_TYPE_FILTER_KEY[
            event.entity_type as keyof typeof ENTITY_TYPE_FILTER_KEY
          ],
        )
      : event.entity_type;

  return (
    <>
      <TableRow data-testid="audit-row">
        <TableCell>
          <button
            type="button"
            onClick={onToggle}
            data-testid="expand-payload"
            className="rounded p-1 hover:bg-muted"
            aria-label={
              expanded
                ? tr("admin.audit.expand.collapse")
                : tr("admin.audit.expand.expand")
            }
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </TableCell>
        <TableCell>
          <Badge variant="outline" data-testid="audit-event-label">
            {eventLabel}
          </Badge>
        </TableCell>
        <TableCell>{entityLabel}</TableCell>
        <TableCell className="font-mono text-xs">{event.entity_id}</TableCell>
        <TableCell className="text-xs text-muted-foreground">
          {formatLocaleDateTime(locale, event.timestamp)}
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
