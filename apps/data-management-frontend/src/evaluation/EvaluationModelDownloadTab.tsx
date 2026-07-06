import { useState } from "react";
import { Download, RefreshCw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";
import { useOllamaModelDownload } from "./useOllamaModelDownload";

export function EvaluationModelDownloadTab() {
  const tr = useAdminT();
  const {
    models,
    modelsLoading,
    modelsError,
    activeModelId,
    downloadStatus,
    downloadError,
    refreshModels,
    downloadModel,
    resetDownloadStatus,
  } = useOllamaModelDownload();
  const [customModelTag, setCustomModelTag] = useState("");

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

      {modelsError ? (
        <p role="alert" className="text-sm text-destructive">
          {modelsError}
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
            disabled={modelsLoading}
            data-testid="eval-models-refresh"
            onClick={() => {
              void refreshModels();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {tr("shared.refresh")}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {modelsLoading && models.length === 0 ? (
            <p className="text-sm text-muted-foreground">{tr("shared.loading")}</p>
          ) : null}
          <ul className="space-y-2" data-testid="eval-models-catalog">
            {models.map((model) => {
              const isPulling =
                downloadStatus === "pulling" &&
                activeModelId === model.model_id;
              return (
                <li
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
                        resetDownloadStatus();
                        void downloadModel(model.model_id);
                      }}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      {isPulling
                        ? tr("admin.evaluation.models.downloadPulling")
                        : tr("admin.evaluation.models.downloadButton")}
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
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
