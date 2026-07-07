import { useCallback, useEffect, useRef, useState } from "react";

import {
  type OllamaModelSummaryApi,
  fetchOllamaModels,
  pullOllamaModel,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";

export const MODEL_PULL_POLL_INTERVAL_MS = 10_000;
export const MODEL_PULL_TIMEOUT_MS = 30 * 60 * 1000;

export type ModelDownloadStatus =
  | "idle"
  | "pulling"
  | "success"
  | "timeout"
  | "error";

export function firstAvailableModelId(
  models: readonly OllamaModelSummaryApi[],
): string | null {
  const match = models.find((model) => model.available);
  return match?.model_id ?? null;
}

export function modelOptionLabel(
  model: OllamaModelSummaryApi,
  notDownloadedLabel: string,
): string {
  if (model.available) {
    return model.model_id;
  }
  return `${model.model_id} ${notDownloadedLabel}`;
}

interface UseOllamaModelDownloadResult {
  models: OllamaModelSummaryApi[];
  modelsLoading: boolean;
  modelsError: string | null;
  activeModelId: string | null;
  downloadStatus: ModelDownloadStatus;
  downloadError: string | null;
  refreshModels: () => Promise<void>;
  downloadModel: (modelId: string) => Promise<void>;
  resetDownloadStatus: () => void;
}

export function useOllamaModelDownload(): UseOllamaModelDownloadResult {
  const [models, setModels] = useState<OllamaModelSummaryApi[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [activeModelId, setActiveModelId] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] =
    useState<ModelDownloadStatus>("idle");
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const downloadPollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const downloadPollStartedAt = useRef<number | null>(null);

  const clearDownloadPoll = useCallback(() => {
    if (downloadPollTimer.current !== null) {
      clearTimeout(downloadPollTimer.current);
      downloadPollTimer.current = null;
    }
    downloadPollStartedAt.current = null;
  }, []);

  const refreshModelsFromApi = useCallback(async (): Promise<
    OllamaModelSummaryApi[]
  > => {
    const client = requireCorpusConfig();
    const data = await fetchOllamaModels(client);
    setModels(data.items);
    return data.items;
  }, []);

  const refreshModels = useCallback(async () => {
    setModelsLoading(true);
    setModelsError(null);
    try {
      await refreshModelsFromApi();
    } catch (err) {
      setModelsError(
        err instanceof Error ? err.message : "Failed to load models",
      );
    } finally {
      setModelsLoading(false);
    }
  }, [refreshModelsFromApi]);

  useEffect(() => {
    void refreshModels();
  }, [refreshModels]);

  useEffect(() => {
    return () => {
      clearDownloadPoll();
    };
  }, [clearDownloadPoll]);

  const scheduleDownloadPoll = useCallback(
    (modelTag: string) => {
      clearDownloadPoll();
      downloadPollStartedAt.current = Date.now();
      const poll = async () => {
        if (downloadPollStartedAt.current === null) return;
        const elapsed = Date.now() - downloadPollStartedAt.current;
        if (elapsed >= MODEL_PULL_TIMEOUT_MS) {
          clearDownloadPoll();
          setDownloadStatus("timeout");
          return;
        }
        try {
          const items = await refreshModelsFromApi();
          const ready = items.some(
            (item) => item.model_id === modelTag && item.available,
          );
          if (ready) {
            clearDownloadPoll();
            setDownloadStatus("success");
            return;
          }
        } catch (err) {
          clearDownloadPoll();
          setDownloadStatus("error");
          setDownloadError(
            err instanceof Error ? err.message : "Model list poll failed",
          );
          return;
        }
        downloadPollTimer.current = setTimeout(() => {
          void poll();
        }, MODEL_PULL_POLL_INTERVAL_MS);
      };
      downloadPollTimer.current = setTimeout(() => {
        void poll();
      }, MODEL_PULL_POLL_INTERVAL_MS);
    },
    [clearDownloadPoll, refreshModelsFromApi],
  );

  const downloadModel = useCallback(
    async (modelId: string) => {
      const tag = modelId.trim();
      if (!tag) return;
      setActiveModelId(tag);
      setDownloadError(null);
      setDownloadStatus("pulling");
      try {
        const client = requireCorpusConfig();
        await pullOllamaModel(client, tag);
        scheduleDownloadPoll(tag);
      } catch (err) {
        clearDownloadPoll();
        setDownloadStatus("error");
        setDownloadError(
          err instanceof Error ? err.message : "Download failed",
        );
      }
    },
    [clearDownloadPoll, scheduleDownloadPoll],
  );

  const resetDownloadStatus = useCallback(() => {
    setDownloadStatus("idle");
    setDownloadError(null);
    setActiveModelId(null);
  }, []);

  return {
    models,
    modelsLoading,
    modelsError,
    activeModelId,
    downloadStatus,
    downloadError,
    refreshModels,
    downloadModel,
    resetDownloadStatus,
  };
}
