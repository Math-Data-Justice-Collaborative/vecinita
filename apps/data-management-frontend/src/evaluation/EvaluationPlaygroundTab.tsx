import { useCallback, useEffect, useMemo, useState } from "react";
import { FlaskConical } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  type EvalRunModeApi,
  type OllamaModelSummaryApi,
  fetchOllamaModels,
  triggerPlaygroundEvalRun,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";

const DEFAULT_TOP_K = 5;
const DEFAULT_MIN_RETRIEVAL_SCORE = 0.2;
const DEFAULT_SYSTEM_PROMPT =
  "Answer community questions using only the context below. Be concise. " +
  "If the context does not answer the question, say you do not have that information.";
const DEFAULT_MAX_TOKENS = 256;
const DEFAULT_TEMPERATURE = 0.2;
const DEFAULT_JUDGE_TEMPERATURE = 0.2;
const DEFAULT_MODEL_ID = "qwen2.5:1.5b-instruct";

export function EvaluationPlaygroundTab() {
  const tr = useAdminT();
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
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRunId, setLastRunId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const loadModels = async () => {
      setModelsLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const data = await fetchOllamaModels(client);
        if (!active) return;
        setModels(data.items ?? []);
        setModelId((current) => {
          const items = data.items ?? [];
          if (items.some((item) => item.model_id === current)) {
            return current;
          }
          return items[0]?.model_id ?? DEFAULT_MODEL_ID;
        });
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof Error
            ? err.message
            : tr("admin.evaluation.playground.loadModelsFailed"),
        );
      } finally {
        if (active) setModelsLoading(false);
      }
    };
    void loadModels();
    return () => {
      active = false;
    };
  }, [tr]);

  const runDisabled = useMemo(() => {
    if (running) return true;
    if (mode === "adhoc" && adhocQuestion.trim().length === 0) return true;
    return false;
  }, [adhocQuestion, mode, running]);

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
        ...(mode === "adhoc" ? { question: adhocQuestion.trim() } : {}),
      });
      setLastRunId(created.run_id);
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
                  <option key={model.model_id} value={model.model_id}>
                    {model.model_id}
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
              <p className="font-mono text-xs" data-testid="eval-playground-last-run">
                {lastRunId}
              </p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
