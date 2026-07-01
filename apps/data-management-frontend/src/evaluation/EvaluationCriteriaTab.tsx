import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  type EvalCriterionApi,
  createEvalCriterion,
  fetchEvalCriteria,
  updateEvalCriterion,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";

export function EvaluationCriteriaTab() {
  const tr = useAdminT();
  const [items, setItems] = useState<EvalCriterionApi[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [slug, setSlug] = useState("");
  const [label, setLabel] = useState("");
  const [rubric, setRubric] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const data = await fetchEvalCriteria(client);
      setItems(data.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.evaluation.criteria.loadFailed"),
      );
    } finally {
      setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleCreate = useCallback(async () => {
    if (!slug.trim() || !label.trim() || !rubric.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      await createEvalCriterion(client, {
        slug: slug.trim(),
        label: label.trim(),
        rubric: rubric.trim(),
      });
      setSlug("");
      setLabel("");
      setRubric("");
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.evaluation.criteria.saveFailed"),
      );
    } finally {
      setSaving(false);
    }
  }, [label, load, rubric, slug, tr]);

  const toggleEnabled = useCallback(
    async (criterion: EvalCriterionApi) => {
      try {
        const client = requireCorpusConfig();
        await updateEvalCriterion(client, criterion.criterion_id, {
          enabled: !criterion.enabled,
        });
        await load();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : tr("admin.evaluation.criteria.saveFailed"),
        );
      }
    },
    [load, tr],
  );

  if (loading) {
    return (
      <div data-testid="evaluation-criteria-tab">
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="evaluation-criteria-tab">
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.evaluation.criteria.addTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm">
              <span>{tr("admin.evaluation.criteria.slug")}</span>
              <input
                className="rounded-md border bg-background px-2 py-1 font-mono text-sm"
                value={slug}
                onChange={(event) => {
                  setSlug(event.target.value);
                }}
                data-testid="eval-criterion-slug"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span>{tr("admin.evaluation.criteria.label")}</span>
              <input
                className="rounded-md border bg-background px-2 py-1 text-sm"
                value={label}
                onChange={(event) => {
                  setLabel(event.target.value);
                }}
                data-testid="eval-criterion-label"
              />
            </label>
          </div>
          <label className="flex flex-col gap-1 text-sm">
            <span>{tr("admin.evaluation.criteria.rubric")}</span>
            <textarea
              className="min-h-24 rounded-md border bg-background px-2 py-1 text-sm"
              value={rubric}
              onChange={(event) => {
                setRubric(event.target.value);
              }}
              data-testid="eval-criterion-rubric"
            />
          </label>
          <Button
            type="button"
            disabled={saving || !slug.trim() || !label.trim() || !rubric.trim()}
            onClick={() => {
              void handleCreate();
            }}
            data-testid="eval-criterion-create"
          >
            <Plus className="mr-2 h-4 w-4" />
            {tr("admin.evaluation.criteria.create")}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.evaluation.criteria.listTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <p className="text-muted-foreground">
              {tr("admin.evaluation.criteria.empty")}
            </p>
          ) : (
            <ul className="space-y-3" data-testid="eval-criteria-list">
              {items.map((item) => (
                <li
                  key={item.criterion_id}
                  className="rounded-md border p-3"
                  data-testid={`eval-criterion-${item.slug}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {item.slug}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={item.enabled ? "default" : "outline"}>
                        {item.enabled
                          ? tr("admin.evaluation.criteria.enabled")
                          : tr("admin.evaluation.criteria.disabled")}
                      </Badge>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          void toggleEnabled(item);
                        }}
                      >
                        {item.enabled
                          ? tr("admin.evaluation.criteria.disable")
                          : tr("admin.evaluation.criteria.enable")}
                      </Button>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{item.rubric}</p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
