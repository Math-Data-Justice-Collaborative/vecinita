import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  type PlaygroundModelCatalogTagApi,
  type PlaygroundModelSummaryApi,
  fetchPlaygroundCatalogFamilies,
  fetchPlaygroundCatalogFamilyTags,
  fetchPlaygroundModels,
  pullPlaygroundModel,
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
  models: readonly PlaygroundModelSummaryApi[],
): string | null {
  const match = models.find((model) => model.available);
  return match?.model_id ?? null;
}

export function modelOptionLabel(
  model: PlaygroundModelSummaryApi,
  notDownloadedLabel: string,
): string {
  if (model.available) {
    return model.model_id;
  }
  return `${model.model_id} ${notDownloadedLabel}`;
}

export interface UsePlaygroundModelDownloadResult {
  models: PlaygroundModelSummaryApi[];
  modelsLoading: boolean;
  modelsError: string | null;
  catalogFamilies: string[];
  catalogLoading: boolean;
  catalogError: string | null;
  familyTags: Readonly<Record<string, PlaygroundModelCatalogTagApi[]>>;
  familyTagsLoading: Readonly<Record<string, boolean>>;
  familyTagsError: Readonly<Record<string, string | null>>;
  activeModelId: string | null;
  downloadStatus: ModelDownloadStatus;
  downloadError: string | null;
  refreshModels: () => Promise<void>;
  refreshCatalog: () => Promise<void>;
  loadFamilyTags: (slug: string) => Promise<void>;
  downloadModel: (modelId: string) => Promise<void>;
  resetDownloadStatus: () => void;
}

const PlaygroundModelDownloadContext =
  createContext<UsePlaygroundModelDownloadResult | null>(null);

function usePlaygroundModelDownloadState(): UsePlaygroundModelDownloadResult & {
  clearDownloadPoll: () => void;
} {
  const [models, setModels] = useState<PlaygroundModelSummaryApi[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [catalogFamilies, setCatalogFamilies] = useState<string[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [familyTags, setFamilyTags] = useState<
    Record<string, PlaygroundModelCatalogTagApi[]>
  >({});
  const [familyTagsLoading, setFamilyTagsLoading] = useState<
    Record<string, boolean>
  >({});
  const [familyTagsError, setFamilyTagsError] = useState<
    Record<string, string | null>
  >({});
  const [activeModelId, setActiveModelId] = useState<string | null>(null);
  const [downloadStatus, setDownloadStatus] =
    useState<ModelDownloadStatus>("idle");
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const downloadPollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const downloadPollStartedAt = useRef<number | null>(null);
  const expandedFamiliesRef = useRef<Set<string>>(new Set());

  const clearDownloadPoll = useCallback(() => {
    if (downloadPollTimer.current !== null) {
      clearTimeout(downloadPollTimer.current);
      downloadPollTimer.current = null;
    }
    downloadPollStartedAt.current = null;
  }, []);

  const refreshModelsFromApi = useCallback(async (): Promise<
    PlaygroundModelSummaryApi[]
  > => {
    const client = requireCorpusConfig();
    const data = await fetchPlaygroundModels(client);
    setModels(data.items);
    return data.items;
  }, []);

  const refreshCatalogFromApi = useCallback(async (): Promise<string[]> => {
    const client = requireCorpusConfig();
    const data = await fetchPlaygroundCatalogFamilies(client);
    const slugs = data.families.map((family) => family.slug);
    setCatalogFamilies(slugs);
    return slugs;
  }, []);

  const loadFamilyTags = useCallback(async (slug: string) => {
    expandedFamiliesRef.current.add(slug);
    setFamilyTagsLoading((current) => ({ ...current, [slug]: true }));
    setFamilyTagsError((current) => ({ ...current, [slug]: null }));
    try {
      const client = requireCorpusConfig();
      const data = await fetchPlaygroundCatalogFamilyTags(client, slug);
      setFamilyTags((current) => ({ ...current, [slug]: data.tags }));
    } catch (err) {
      setFamilyTagsError((current) => ({
        ...current,
        [slug]:
          err instanceof Error ? err.message : "Failed to load model tags",
      }));
    } finally {
      setFamilyTagsLoading((current) => ({ ...current, [slug]: false }));
    }
  }, []);

  const refreshExpandedFamilyTags = useCallback(async () => {
    const slugs = [...expandedFamiliesRef.current];
    await Promise.all(slugs.map((slug) => loadFamilyTags(slug)));
  }, [loadFamilyTags]);

  const refreshModels = useCallback(async () => {
    setModelsLoading(true);
    setModelsError(null);
    try {
      await refreshModelsFromApi();
      await refreshExpandedFamilyTags();
    } catch (err) {
      setModelsError(
        err instanceof Error ? err.message : "Failed to load models",
      );
    } finally {
      setModelsLoading(false);
    }
  }, [refreshExpandedFamilyTags, refreshModelsFromApi]);

  const refreshCatalog = useCallback(async () => {
    setCatalogLoading(true);
    setCatalogError(null);
    try {
      await refreshCatalogFromApi();
      await refreshExpandedFamilyTags();
    } catch (err) {
      setCatalogError(
        err instanceof Error ? err.message : "Failed to load playground catalog",
      );
    } finally {
      setCatalogLoading(false);
    }
  }, [refreshCatalogFromApi, refreshExpandedFamilyTags]);

  useEffect(() => {
    void refreshModels();
  }, [refreshModels]);

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
          await refreshExpandedFamilyTags();
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
    [clearDownloadPoll, refreshExpandedFamilyTags, refreshModelsFromApi],
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
        await pullPlaygroundModel(client, tag);
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
    catalogFamilies,
    catalogLoading,
    catalogError,
    familyTags,
    familyTagsLoading,
    familyTagsError,
    activeModelId,
    downloadStatus,
    downloadError,
    refreshModels,
    refreshCatalog,
    loadFamilyTags,
    downloadModel,
    resetDownloadStatus,
    clearDownloadPoll,
  };
}

export function PlaygroundModelDownloadProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { clearDownloadPoll, ...value } = usePlaygroundModelDownloadState();

  useEffect(() => {
    return () => {
      clearDownloadPoll();
    };
  }, [clearDownloadPoll]);

  return (
    <PlaygroundModelDownloadContext.Provider value={value}>
      {children}
    </PlaygroundModelDownloadContext.Provider>
  );
}

export function usePlaygroundModelDownload(): UsePlaygroundModelDownloadResult {
  const context = useContext(PlaygroundModelDownloadContext);
  if (context === null) {
    throw new Error(
      "usePlaygroundModelDownload must be used within PlaygroundModelDownloadProvider",
    );
  }
  return context;
}
