import { type EvalRunDetailApi } from "@/api/admin";

/** Placeholder until T69.5 implements side-by-side compare (TC-130). */
export function EvaluationCompareView(_props: {
  runA: EvalRunDetailApi;
  runB: EvalRunDetailApi;
}) {
  return <div data-testid="evaluation-compare" />;
}
