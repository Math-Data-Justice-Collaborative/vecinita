import { useEffect, useState } from "react";
import { ChevronRight, Download, RefreshCw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";
import { useOllamaModelDownload } from "./useOllamaModelDownload";

function CatalogFamilyRow({
  slug,
  tags,
  tagsLoading,
  tagsError,
  activeModelId,
  downloadStatus,
  onExpand,
  onDownload,
  onResetDownloadStatus,
}: {
  slug: string;
  tags: readonly { model_id: string; available: boolean }[] | undefined;
  tagsLoading: boolean;
  tagsError: string | null | undefined;
  activeModelId: string | null;
  downloadStatus: string;
  onExpand: (slug: string) => void;
  onDownload: (modelId: string) => void;
  onResetDownloadStatus: () => void;
}) {
  const tr = useAdminT();

  return (
    <details
      className="group rounded-md border"
      data-testid={`eval-models-family-${slug}`}
      onToggle={(event) => {
        if (event.currentTarget.open) {
          onExpand(slug);
        }
      }}
    >
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 font-mono text-sm font-semibold [&::-webkit-details-marker]:hidden">
        <ChevronRight className="h-4 w-4 shrink-0 transition-transform group-open:rotate-90" />
        {slug}
      </summary>
      <div className="space-y-2 border-t px-3 py-2" data-testid={`eval-models-tags-${slug}`}>
        {tagsLoading ? (
          <p className="text-sm text-muted-foreground">{tr("shared.loading")}</p>
        ) : null}
        {tagsError ? (
          <p role="alert" className="text-sm text-destructive">
            {tagsError}
          </p>
        ) : null}
        {tags?.map((model) => {
          const isPulling =
            downloadStatus === "pulling" && activeModelId === model.model_id;
          return (
            <div
              key={model.model_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2"
              data-testid={`eval-models-row-${model.model_id}`}
            >
              <span className="font-mono text-sm">{model.model_id}</span>
              <div className="flex items-center gap-2">
                <Badge
                  variant={model.available ? "default" : "secondary"}
                  data-testid={`eval-models-status-${model.model_id}`}
                >
                  {model.available
                    ? tr("admin.evaluation.models.statusAvailable")
                    : tr("admin.evaluation.models.statusNotDownloaded")}
                </Badge>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={model.available || isPulling}
                  data-testid={`eval-models-download-${model.model_id}`}
                  onClick={() => {
                    onResetDownloadStatus();
                    onDownload(model.model_id);
                  }}
                >
                  <Download className="mr-2 h-4 w-4" />
                  {isPulling
                    ? tr("admin.evaluation.models.downloadPulling")
                    : tr("admin.evaluation.models.downloadButton")}
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </details>
  );
}

export function EvaluationModelDownloadTab() {
  const tr = useAdminT();
  const {
    catalogFamilies,
    catalogLoading,
    catalogError,
    familyTags,
    familyTagsLoading,
    familyTagsError,
    activeModelId,
    downloadStatus,
    downloadError,
    refreshCatalog,
    loadFamilyTags,
    downloadModel,
    resetDownloadStatus,
  } = useOllamaModelDownload();
  const [customModelTag, setCustomModelTag] = useState("");

  useEffect(() => {
    void refreshCatalog();
  }, [refreshCatalog]);

  const statusMessage = (() => {
    if (downloadStatus === "idle") {
      return tr("admin.evaluation.models.downloadStatusIdle");
    }
    if (downloadStatus === "pulling") {
      return tr("admin.evaluation.models.downloadStatusPulling");
    }
    if (downloadStatus === "success") {
      return tr("admin.evaluation.models.downloadStatusSuccess");
    }
    if (downloadStatus === "timeout") {
      return tr("admin.evaluation.models.downloadStatusTimeout");
    }
    return downloadError ?? tr("admin.evaluation.models.downloadFailed");
  })();

  return (
    <div className="space-y-4" data-testid="evaluation-models-download">
      <div>
        <h3 className="text-xl font-semibold">
          {tr("admin.evaluation.models.title")}
        </h3>
        <p className="text-sm text-muted-foreground">
          {tr("admin.evaluation.models.subtitle")}
        </p>
      </div>

      {catalogError ? (
        <p role="alert" className="text-sm text-destructive">
          {catalogError}
        </p>
      ) : null}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <CardTitle className="text-base">
            {tr("admin.evaluation.models.catalogTitle")}
          </CardTitle>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={catalogLoading}
            data-testid="eval-models-refresh"
            onClick={() => {
              void refreshCatalog();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {tr("shared.refresh")}
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {tr("admin.evaluation.models.catalogTreeHint")}
          </p>
          {catalogLoading && catalogFamilies.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {tr("shared.loading")}
            </p>
          ) : null}
          <div className="space-y-2" data-testid="eval-models-catalog">
            {catalogFamilies.map((slug) => (
              <CatalogFamilyRow
                key={slug}
                slug={slug}
                tags={familyTags[slug]}
                tagsLoading={familyTagsLoading[slug] ?? false}
                tagsError={familyTagsError[slug]}
                activeModelId={activeModelId}
                downloadStatus={downloadStatus}
                onExpand={(familySlug) => {
                  void loadFamilyTags(familySlug);
                }}
                onDownload={(modelId) => {
                  void downloadModel(modelId);
                }}
                onResetDownloadStatus={resetDownloadStatus}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <Card data-testid="eval-models-custom-download-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">
            {tr("admin.evaluation.models.customTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {tr("admin.evaluation.models.customHint")}
          </p>
          <div className="space-y-2">
            <Label htmlFor="eval-models-custom-model-id">
              {tr("admin.evaluation.models.customModelLabel")}
            </Label>
            <input
              id="eval-models-custom-model-id"
              data-testid="eval-models-custom-model-id"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={customModelTag}
              disabled={downloadStatus === "pulling"}
              placeholder={tr("admin.evaluation.models.customModelPlaceholder")}
              onChange={(event) => {
                setCustomModelTag(event.target.value);
              }}
            />
          </div>
          <Button
            type="button"
            size="sm"
            data-testid="eval-models-custom-download-button"
            disabled={
              downloadStatus === "pulling" || customModelTag.trim().length === 0
            }
            onClick={() => {
              resetDownloadStatus();
              void downloadModel(customModelTag);
            }}
          >
            {downloadStatus === "pulling"
              ? tr("admin.evaluation.models.downloadPulling")
              : tr("admin.evaluation.models.downloadButton")}
          </Button>
          <p
            className="text-sm text-muted-foreground"
            data-testid="eval-models-download-status"
          >
            {downloadStatus !== "idle" ? statusMessage : null}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
