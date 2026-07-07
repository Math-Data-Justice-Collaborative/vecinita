import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Copy, FlaskConical, Rocket, Save } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AuthContext } from "@/auth/authContext";
import {
  type EvalConfigApi,
  type EvalConfigPresetApi,
  type EvalRunModeApi,
  type OllamaModelSummaryApi,
  cloneEvalConfigPreset,
  createEvalConfigPreset,
  fetchEvalConfigPresets,
  fetchOllamaModels,
  promoteRagConfig,
  triggerPlaygroundEvalRun,
  updateEvalConfigPreset,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import {
  loadEvalPlaygroundPreferences,
  saveEvalPlaygroundLastPresetId,
} from "./evalPlaygroundStorage";
import {
  firstAvailableModelId,
  modelOptionLabel,
} from "./useOllamaModelDownload";

const DEFAULT_TOP_K = 5;
const DEFAULT_MIN_RETRIEVAL_SCORE = 0.2;
const DEFAULT_SYSTEM_PROMPT =
  "Answer community questions using only the context below. Be concise. " +
  "If the context does not answer the question, say you do not have that information.";
const DEFAULT_MAX_TOKENS = 256;
const DEFAULT_TEMPERATURE = 0.2;
const DEFAULT_JUDGE_TEMPERATURE = 0.2;
const DEFAULT_MODEL_ID = "qwen2.5:1.5b-instruct";

/** vLLM-only deployments omit Modal Ollama; playground still needs a selectable model tag. */
const VLLM_FALLBACK_MODELS: readonly OllamaModelSummaryApi[] = [
  { model_id: DEFAULT_MODEL_ID, available: true },
];

function isOllamaModelsUnavailableError(err: unknown): boolean {
  if (!(err instanceof Error)) {
    return false;
  }
  return /\((502|503|504)\)/.test(err.message);
}

function buildFullConfig(input: {
  topK: number;
  minRetrievalScore: number;
  systemPrompt: string;
  maxTokens: number;
  temperature: number;
  judgeTemperature: number;
  corpusProfile: "fixture" | "staging";
  modelId: string;
}): EvalConfigApi {
  return {
    top_k: input.topK,
    min_retrieval_score: input.minRetrievalScore,
    system_prompt: input.systemPrompt,
    max_tokens: input.maxTokens,
    temperature: input.temperature,
    judge_temperature: input.judgeTemperature,
    corpus_profile: input.corpusProfile,
    model_id: input.modelId,
    criteria_ids: [],
  };
}

function applyConfigToForm(
  config: EvalConfigApi,
  setters: {
    setTopK: (value: number) => void;
    setMinRetrievalScore: (value: number) => void;
    setSystemPrompt: (value: string) => void;
    setMaxTokens: (value: number) => void;
    setTemperature: (value: number) => void;
    setJudgeTemperature: (value: number) => void;
    setCorpusProfile: (value: "fixture" | "staging") => void;
    setModelId: (value: string) => void;
  },
): void {
  setters.setTopK(config.top_k);
  setters.setMinRetrievalScore(config.min_retrieval_score);
  setters.setSystemPrompt(config.system_prompt);
  setters.setMaxTokens(config.max_tokens);
  setters.setTemperature(config.temperature);
  setters.setJudgeTemperature(config.judge_temperature);
  setters.setCorpusProfile(config.corpus_profile);
  setters.setModelId(config.model_id);
}

export interface EvaluationPlaygroundTabProps {
  onRunCreated?: (runId: string) => void;
}

export function EvaluationPlaygroundTab({
  onRunCreated,
}: EvaluationPlaygroundTabProps) {
  const tr = useAdminT();
  const authCtx = useContext(AuthContext);
  const user = authCtx?.user ?? null;
  const isSuperAdmin = authCtx?.role === "super-admin";
  const [mode, setMode] = useState<EvalRunModeApi>("golden");
  const [topK, setTopK] = useState(DEFAULT_TOP_K);
  const [minRetrievalScore, setMinRetrievalScore] = useState(
    DEFAULT_MIN_RETRIEVAL_SCORE,
  );
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [maxTokens, setMaxTokens] = useState(DEFAULT_MAX_TOKENS);
  const [temperature, setTemperature] = useState(DEFAULT_TEMPERATURE);
  const [judgeTemperature, setJudgeTemperature] = useState(
    DEFAULT_JUDGE_TEMPERATURE,
  );
  const [corpusProfile, setCorpusProfile] = useState<"fixture" | "staging">(
    "fixture",
  );
  const [modelId, setModelId] = useState(DEFAULT_MODEL_ID);
  const [adhocQuestion, setAdhocQuestion] = useState("");
  const [models, setModels] = useState<OllamaModelSummaryApi[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [presets, setPresets] = useState<EvalConfigPresetApi[]>([]);
  const [presetsLoading, setPresetsLoading] = useState(true);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");
  const [presetDialogOpen, setPresetDialogOpen] = useState(false);
  const [presetDialogMode, setPresetDialogMode] = useState<"create" | "update">(
    "create",
  );
  const [presetName, setPresetName] = useState("");
  const [presetShared, setPresetShared] = useState(false);
  const [presetSaving, setPresetSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const [promoteDialogOpen, setPromoteDialogOpen] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [promoteVersion, setPromoteVersion] = useState<number | null>(null);
  const initialPresetApplied = useRef(false);

  const selectedPreset = useMemo(
    () =>
      presets.find((preset) => preset.preset_id === selectedPresetId) ?? null,
    [presets, selectedPresetId],
  );

  const isPresetOwner = useMemo(() => {
    if (!selectedPreset || !user?.id) return false;
    return selectedPreset.owner_id === user.id;
  }, [selectedPreset, user?.id]);

  const canClonePreset = useMemo(() => {
    if (!selectedPreset || !user?.id) return false;
    return selectedPreset.owner_id !== user.id && selectedPreset.shared;
  }, [selectedPreset, user?.id]);

  const formSetters = useMemo(
    () => ({
      setTopK,
      setMinRetrievalScore,
      setSystemPrompt,
      setMaxTokens,
      setTemperature,
      setJudgeTemperature,
      setCorpusProfile,
      setModelId,
    }),
    [],
  );

  const currentConfig = useMemo(
    () =>
      buildFullConfig({
        topK,
        minRetrievalScore,
        systemPrompt,
        maxTokens,
        temperature,
        judgeTemperature,
        corpusProfile,
        modelId,
      }),
    [
      corpusProfile,
      judgeTemperature,
      maxTokens,
      minRetrievalScore,
      modelId,
      systemPrompt,
      temperature,
      topK,
    ],
  );

  const loadPresets = useCallback(async () => {
    setPresetsLoading(true);
    try {
      const client = requireCorpusConfig();
      const data = await fetchEvalConfigPresets(client);
      setPresets(Array.isArray(data.items) ? data.items : []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.playground.presetsLoadFailed"),
      );
    } finally {
      setPresetsLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    let active = true;
    const loadModels = async () => {
      setModelsLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const data = await fetchOllamaModels(client);
        if (!active) return;
        setModels(data.items);
        setModelId((current) => {
          const currentModel = data.items.find(
            (item) => item.model_id === current,
          );
          if (currentModel?.available) {
            return current;
          }
          return (
            firstAvailableModelId(data.items) ??
            data.items[0]?.model_id ??
            DEFAULT_MODEL_ID
          );
        });
      } catch (err) {
        if (!active) return;
        if (isOllamaModelsUnavailableError(err)) {
          setModels([...VLLM_FALLBACK_MODELS]);
          setModelId(DEFAULT_MODEL_ID);
        } else {
          setError(
            err instanceof Error
              ? err.message
              : tr("admin.evaluation.playground.loadModelsFailed"),
          );
        }
      } finally {
        if (active) setModelsLoading(false);
      }
    };
    void loadModels();
    void loadPresets();
    return () => {
      active = false;
    };
  }, [loadPresets, tr]);

  useEffect(() => {
    if (presetsLoading || initialPresetApplied.current) return;
    initialPresetApplied.current = true;
    const lastPresetId = loadEvalPlaygroundPreferences().lastPresetId;
    if (!lastPresetId) return;
    const preset = presets.find((item) => item.preset_id === lastPresetId);
    if (!preset) return;
    setSelectedPresetId(lastPresetId);
    applyConfigToForm(preset.config, formSetters);
  }, [formSetters, presets, presetsLoading]);

  const handlePresetSelect = useCallback(
    (presetId: string) => {
      setSelectedPresetId(presetId);
      saveEvalPlaygroundLastPresetId(presetId || null);
      if (!presetId) return;
      const preset = presets.find((item) => item.preset_id === presetId);
      if (!preset) return;
      applyConfigToForm(preset.config, formSetters);
    },
    [formSetters, presets],
  );

  const openCreatePresetDialog = useCallback(() => {
    setPresetDialogMode("create");
    setPresetName("");
    setPresetShared(false);
    setPresetDialogOpen(true);
  }, []);

  const openUpdatePresetDialog = useCallback(() => {
    if (!selectedPreset) return;
    setPresetDialogMode("update");
    setPresetName(selectedPreset.name);
    setPresetShared(selectedPreset.shared);
    setPresetDialogOpen(true);
  }, [selectedPreset]);

  const handleSavePreset = useCallback(async () => {
    setPresetSaving(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      if (presetDialogMode === "update" && selectedPreset) {
        const updated = await updateEvalConfigPreset(
          client,
          selectedPreset.preset_id,
          {
            name: presetName.trim(),
            config: currentConfig,
            shared: presetShared,
          },
        );
        setPresets((current) =>
          current.map((item) =>
            item.preset_id === updated.preset_id ? updated : item,
          ),
        );
        setSelectedPresetId(updated.preset_id);
        saveEvalPlaygroundLastPresetId(updated.preset_id);
      } else {
        const created = await createEvalConfigPreset(client, {
          name: presetName.trim(),
          config: currentConfig,
          shared: presetShared,
        });
        setPresets((current) => [created, ...current]);
        setSelectedPresetId(created.preset_id);
        saveEvalPlaygroundLastPresetId(created.preset_id);
      }
      setPresetDialogOpen(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.playground.presetsSaveFailed"),
      );
    } finally {
      setPresetSaving(false);
    }
  }, [
    currentConfig,
    presetDialogMode,
    presetName,
    presetShared,
    selectedPreset,
    tr,
  ]);

  const handleClonePreset = useCallback(async () => {
    if (!selectedPreset) return;
    setPresetSaving(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const cloned = await cloneEvalConfigPreset(
        client,
        selectedPreset.preset_id,
        `${selectedPreset.name} (copy)`,
      );
      setPresets((current) => [cloned, ...current]);
      setSelectedPresetId(cloned.preset_id);
      saveEvalPlaygroundLastPresetId(cloned.preset_id);
      applyConfigToForm(cloned.config, formSetters);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.playground.presetsCloneFailed"),
      );
    } finally {
      setPresetSaving(false);
    }
  }, [formSetters, selectedPreset, tr]);

  const runDisabled = useMemo(() => {
    if (running) return true;
    if (mode === "adhoc" && adhocQuestion.trim().length === 0) return true;
    return false;
  }, [adhocQuestion, mode, running]);

  const promoteDisabled = useMemo(() => {
    if (promoting) return true;
    return !selectedPresetId && !lastRunId;
  }, [lastRunId, promoting, selectedPresetId]);

  const handlePromote = useCallback(async () => {
    setPromoting(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const body = selectedPresetId
        ? { source: "preset" as const, preset_id: selectedPresetId }
        : { source: "run" as const, run_id: lastRunId ?? "" };
      const result = await promoteRagConfig(client, body);
      setPromoteVersion(result.config_version);
      setPromoteDialogOpen(false);
    } catch (err) {
      setPromoteDialogOpen(false);
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.playground.promoteFailed"),
      );
    } finally {
      setPromoting(false);
    }
  }, [lastRunId, selectedPresetId, tr]);

  const handleRun = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const config = {
        top_k: topK,
        min_retrieval_score: minRetrievalScore,
        system_prompt: systemPrompt,
        max_tokens: maxTokens,
        temperature,
        judge_temperature: judgeTemperature,
        corpus_profile: corpusProfile,
        model_id: modelId,
      };
      const created = await triggerPlaygroundEvalRun(client, {
        mode,
        config,
        ...(selectedPresetId ? { preset_id: selectedPresetId } : {}),
        ...(mode === "adhoc" ? { question: adhocQuestion.trim() } : {}),
      });
      setLastRunId(created.run_id);
      if (selectedPresetId) {
        saveEvalPlaygroundLastPresetId(selectedPresetId);
      }
      onRunCreated?.(created.run_id);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.playground.runFailed"),
      );
    } finally {
      setRunning(false);
    }
  }, [
    adhocQuestion,
    corpusProfile,
    judgeTemperature,
    maxTokens,
    minRetrievalScore,
    mode,
    modelId,
    onRunCreated,
    selectedPresetId,
    systemPrompt,
    temperature,
    topK,
    tr,
  ]);

  return (
    <div className="space-y-4" data-testid="evaluation-playground">
      <div>
        <h3 className="text-xl font-semibold">
          {tr("admin.evaluation.playground.title")}
        </h3>
        <p className="text-sm text-muted-foreground">
          {tr("admin.evaluation.playground.subtitle")}
        </p>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card data-testid="eval-playground-config-column">
          <CardHeader>
            <CardTitle>{tr("admin.evaluation.playground.title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <fieldset
              className="space-y-3 rounded-md border p-3"
              data-testid="eval-playground-presets"
            >
              <legend className="px-1 text-sm font-medium">
                {tr("admin.evaluation.playground.presetsTitle")}
              </legend>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-preset-select">
                  {tr("admin.evaluation.playground.presetsLoad")}
                </Label>
                <select
                  id="eval-playground-preset-select"
                  data-testid="eval-playground-preset-select"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={selectedPresetId}
                  disabled={presetsLoading}
                  onChange={(event) => {
                    handlePresetSelect(event.target.value);
                  }}
                >
                  <option value="">
                    {tr("admin.evaluation.playground.presetsNone")}
                  </option>
                  {presets.map((preset) => (
                    <option key={preset.preset_id} value={preset.preset_id}>
                      {preset.name} (v{preset.version}
                      {preset.shared ? ", shared" : ""})
                    </option>
                  ))}
                </select>
              </div>
              {selectedPreset ? (
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <Badge
                    variant="secondary"
                    data-testid="eval-playground-preset-version"
                  >
                    {tr("admin.evaluation.playground.presetsVersion", {
                      version: String(selectedPreset.version),
                    })}
                  </Badge>
                  {selectedPreset.shared ? (
                    <Badge variant="outline">
                      {isPresetOwner
                        ? tr("admin.evaluation.playground.presetsShared")
                        : tr(
                            "admin.evaluation.playground.presetsSharedByOther",
                          )}
                    </Badge>
                  ) : null}
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  data-testid="eval-playground-preset-save"
                  onClick={openCreatePresetDialog}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {tr("admin.evaluation.playground.presetsSave")}
                </Button>
                {isPresetOwner ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    data-testid="eval-playground-preset-update"
                    onClick={openUpdatePresetDialog}
                  >
                    {tr("admin.evaluation.playground.presetsUpdate")}
                  </Button>
                ) : null}
                {canClonePreset ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={presetSaving}
                    data-testid="eval-playground-preset-clone"
                    onClick={() => {
                      void handleClonePreset();
                    }}
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    {tr("admin.evaluation.playground.presetsClone")}
                  </Button>
                ) : null}
              </div>
            </fieldset>

            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">
                {tr("admin.evaluation.playground.modeGolden")}
              </legend>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={mode === "golden" ? "default" : "outline"}
                  data-testid="eval-playground-mode-golden"
                  onClick={() => {
                    setMode("golden");
                  }}
                >
                  {tr("admin.evaluation.playground.modeGolden")}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={mode === "adhoc" ? "default" : "outline"}
                  data-testid="eval-playground-mode-adhoc"
                  onClick={() => {
                    setMode("adhoc");
                  }}
                >
                  {tr("admin.evaluation.playground.modeAdhoc")}
                </Button>
              </div>
            </fieldset>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="eval-playground-top-k">
                  {tr("admin.evaluation.playground.topK")}
                </Label>
                <input
                  id="eval-playground-top-k"
                  data-testid="eval-playground-top-k"
                  type="number"
                  min={1}
                  max={50}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={topK}
                  onChange={(event) => {
                    setTopK(Number(event.target.value));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-min-score">
                  {tr("admin.evaluation.playground.minRetrievalScore")}
                </Label>
                <input
                  id="eval-playground-min-score"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={minRetrievalScore}
                  onChange={(event) => {
                    setMinRetrievalScore(Number(event.target.value));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-max-tokens">
                  {tr("admin.evaluation.playground.maxTokens")}
                </Label>
                <input
                  id="eval-playground-max-tokens"
                  type="number"
                  min={1}
                  max={1024}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={maxTokens}
                  onChange={(event) => {
                    setMaxTokens(Number(event.target.value));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-temperature">
                  {tr("admin.evaluation.playground.temperature")}
                </Label>
                <input
                  id="eval-playground-temperature"
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={temperature}
                  onChange={(event) => {
                    setTemperature(Number(event.target.value));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-judge-temperature">
                  {tr("admin.evaluation.playground.judgeTemperature")}
                </Label>
                <input
                  id="eval-playground-judge-temperature"
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={judgeTemperature}
                  onChange={(event) => {
                    setJudgeTemperature(Number(event.target.value));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="eval-playground-corpus-profile">
                  {tr("admin.evaluation.playground.corpusProfile")}
                </Label>
                <select
                  id="eval-playground-corpus-profile"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={corpusProfile}
                  onChange={(event) => {
                    setCorpusProfile(
                      event.target.value === "staging" ? "staging" : "fixture",
                    );
                  }}
                >
                  <option value="fixture">fixture</option>
                  <option value="staging">staging</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="eval-playground-model-id">
                {tr("admin.evaluation.playground.modelId")}
              </Label>
              <select
                id="eval-playground-model-id"
                data-testid="eval-playground-model-id"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={modelId}
                disabled={modelsLoading}
                onChange={(event) => {
                  setModelId(event.target.value);
                }}
              >
                {models.map((model) => (
                  <option
                    key={model.model_id}
                    value={model.model_id}
                    disabled={!model.available}
                  >
                    {modelOptionLabel(
                      model,
                      tr("admin.evaluation.playground.modelNotDownloaded"),
                    )}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="eval-playground-system-prompt">
                {tr("admin.evaluation.playground.systemPrompt")}
              </Label>
              <textarea
                id="eval-playground-system-prompt"
                data-testid="eval-playground-system-prompt"
                className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={systemPrompt}
                onChange={(event) => {
                  setSystemPrompt(event.target.value);
                }}
              />
            </div>

            {mode === "adhoc" ? (
              <div className="space-y-2">
                <Label htmlFor="eval-playground-adhoc-question">
                  {tr("admin.evaluation.playground.adhocQuestion")}
                </Label>
                <textarea
                  id="eval-playground-adhoc-question"
                  data-testid="eval-playground-adhoc-question"
                  className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={adhocQuestion}
                  onChange={(event) => {
                    setAdhocQuestion(event.target.value);
                  }}
                />
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card data-testid="eval-playground-run-column">
          <CardHeader>
            <CardTitle>{tr("admin.evaluation.playground.recentRun")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              type="button"
              disabled={runDisabled}
              data-testid="eval-playground-run-button"
              onClick={() => {
                void handleRun();
              }}
            >
              <FlaskConical className="mr-2 h-4 w-4" />
              {running
                ? tr("admin.evaluation.playground.running")
                : tr("admin.evaluation.playground.run")}
            </Button>
            {lastRunId ? (
              <p
                className="font-mono text-xs"
                data-testid="eval-playground-last-run"
              >
                {lastRunId}
              </p>
            ) : null}
            {isSuperAdmin ? (
              <>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={promoteDisabled}
                  data-testid="eval-playground-promote-button"
                  onClick={() => {
                    setPromoteDialogOpen(true);
                  }}
                >
                  <Rocket className="mr-2 h-4 w-4" />
                  {tr("admin.evaluation.playground.promote")}
                </Button>
                {promoteVersion !== null ? (
                  <p
                    className="text-xs text-muted-foreground"
                    data-testid="eval-playground-promote-version"
                  >
                    {tr("admin.evaluation.playground.promoteVersion", {
                      version: promoteVersion,
                    })}
                  </p>
                ) : null}
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Dialog open={promoteDialogOpen} onOpenChange={setPromoteDialogOpen}>
        <DialogContent data-testid="eval-playground-promote-dialog">
          <DialogHeader>
            <DialogTitle>
              {tr("admin.evaluation.playground.promoteDialogTitle")}
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            {tr("admin.evaluation.playground.promoteDialogBody")}
          </p>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setPromoteDialogOpen(false);
              }}
            >
              {tr("shared.cancel")}
            </Button>
            <Button
              type="button"
              disabled={promoting}
              data-testid="eval-playground-promote-confirm"
              onClick={() => {
                void handlePromote();
              }}
            >
              {promoting
                ? tr("admin.evaluation.playground.promoting")
                : tr("admin.evaluation.playground.promoteConfirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={presetDialogOpen} onOpenChange={setPresetDialogOpen}>
        <DialogContent data-testid="eval-playground-preset-dialog">
          <DialogHeader>
            <DialogTitle>
              {presetDialogMode === "update"
                ? tr("admin.evaluation.playground.presetsUpdateDialogTitle")
                : tr("admin.evaluation.playground.presetsSaveDialogTitle")}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="eval-playground-preset-name">
                {tr("admin.evaluation.playground.presetsName")}
              </Label>
              <input
                id="eval-playground-preset-name"
                data-testid="eval-playground-preset-name"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={presetName}
                onChange={(event) => {
                  setPresetName(event.target.value);
                }}
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="eval-playground-preset-shared"
                data-testid="eval-playground-preset-shared"
                checked={presetShared}
                onCheckedChange={(checked) => {
                  setPresetShared(checked === true);
                }}
              />
              <Label htmlFor="eval-playground-preset-shared">
                {tr("admin.evaluation.playground.presetsShareRead")}
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setPresetDialogOpen(false);
              }}
            >
              {tr("shared.cancel")}
            </Button>
            <Button
              type="button"
              disabled={presetSaving || !presetName.trim()}
              data-testid="eval-playground-preset-confirm"
              onClick={() => {
                void handleSavePreset();
              }}
            >
              {presetDialogMode === "update"
                ? tr("admin.evaluation.playground.presetsUpdate")
                : tr("admin.evaluation.playground.presetsSave")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
