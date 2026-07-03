import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { type EvalRunDetailApi } from "@/api/admin";

import { EvaluationCompareView } from "@/evaluation/EvaluationCompareView";

const RUN_A_ID = "00000000-0000-0000-0000-0000000000aa";
const RUN_B_ID = "00000000-0000-0000-0000-0000000000bb";

const RUN_A: EvalRunDetailApi = {
  run_id: RUN_A_ID,
  status: "completed",
  metrics_summary: {
    retrieval_relevance: 0.91,
    faithfulness: 0.85,
    answer_relevancy: 0.8,
    latency_p95_ms: 3200,
  },
  items: [
    {
      case_id: "community-food-pantry",
      locale: "en",
      question: "When are food pantry hours updated?",
      retrieved_urls: ["fixture://corpus/en/community-resources.md"],
      answer: "Food pantry hours are posted weekly.",
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.85,
        answer_relevancy: 0.8,
        latency_ms: 3100,
      },
    },
    {
      case_id: "retrieval-miss",
      locale: "en",
      question: "Where is the wrong document?",
      retrieved_urls: [],
      answer: null,
      metrics: {
        retrieval_pass: false,
        faithfulness: 0.4,
        answer_relevancy: 0.3,
        latency_ms: 900,
      },
    },
  ],
};

const RUN_B: EvalRunDetailApi = {
  run_id: RUN_B_ID,
  status: "completed",
  metrics_summary: {
    retrieval_relevance: 0.88,
    faithfulness: 0.55,
    answer_relevancy: 0.72,
    latency_p95_ms: 4100,
  },
  items: [
    {
      case_id: "community-food-pantry",
      locale: "en",
      question: "When are food pantry hours updated?",
      retrieved_urls: ["fixture://corpus/en/community-resources.md"],
      answer: "Hours update every Monday morning.",
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.55,
        answer_relevancy: 0.72,
        latency_ms: 3900,
      },
    },
    {
      case_id: "retrieval-miss",
      locale: "en",
      question: "Where is the wrong document?",
      retrieved_urls: [],
      answer: null,
      metrics: {
        retrieval_pass: false,
        faithfulness: 0.35,
        answer_relevancy: 0.25,
        latency_ms: 1100,
      },
    },
  ],
};

const ADHOC_RUN: EvalRunDetailApi = {
  run_id: "00000000-0000-0000-0000-0000000000cc",
  status: "completed",
  metrics_summary: {
    retrieval_relevance: 1,
    faithfulness: 0.9,
    answer_relevancy: 0.88,
    latency_p95_ms: 1800,
  },
  items: [
    {
      case_id: "adhoc",
      locale: "en",
      question: "Is the community center open on Sundays?",
      retrieved_urls: ["fixture://corpus/en/community-resources.md"],
      answer: "Yes, the community center is open Sundays 10am–2pm.",
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.9,
        answer_relevancy: 0.88,
        latency_ms: 1800,
      },
    },
  ],
};

function renderCompare(runA: EvalRunDetailApi, runB: EvalRunDetailApi) {
  return render(
    <LocaleProvider>
      <EvaluationCompareView runA={runA} runB={runB} />
    </LocaleProvider>,
  );
}

function compareRoot() {
  return within(screen.getByTestId("evaluation-compare"));
}

describe("EvaluationCompareView (UJ-046)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders side-by-side compare container (TC-130)", () => {
    renderCompare(RUN_A, RUN_B);
    expect(screen.getByTestId("evaluation-compare")).toBeInTheDocument();
    expect(
      compareRoot().getByTestId("eval-compare-run-a-label"),
    ).toHaveTextContent(RUN_A_ID);
    expect(
      compareRoot().getByTestId("eval-compare-run-b-label"),
    ).toHaveTextContent(RUN_B_ID);
  });

  it("shows aggregate metric deltas between two runs (TC-130)", () => {
    renderCompare(RUN_A, RUN_B);
    const faithfulnessDelta = compareRoot().getByTestId(
      "eval-compare-metric-faithfulness",
    );
    expect(faithfulnessDelta).toHaveTextContent("0.85");
    expect(faithfulnessDelta).toHaveTextContent("0.55");
    expect(faithfulnessDelta).toHaveTextContent("-0.30");

    const retrievalDelta = compareRoot().getByTestId(
      "eval-compare-metric-retrieval",
    );
    expect(retrievalDelta).toHaveTextContent("91%");
    expect(retrievalDelta).toHaveTextContent("88%");
  });

  it("matches per-question rows by case_id (TC-130)", () => {
    renderCompare(RUN_A, RUN_B);
    const pantryRow = compareRoot().getByTestId(
      "eval-compare-row-community-food-pantry",
    );
    expect(pantryRow).toHaveTextContent("When are food pantry hours updated?");
    expect(pantryRow).toHaveTextContent("Food pantry hours are posted weekly.");
    expect(pantryRow).toHaveTextContent("Hours update every Monday morning.");
    expect(pantryRow).toHaveTextContent("0.85");
    expect(pantryRow).toHaveTextContent("0.55");
  });

  it("highlights metric regressions below display threshold (TC-130)", () => {
    renderCompare(RUN_A, RUN_B);
    expect(
      compareRoot().getByTestId(
        "eval-compare-regression-community-food-pantry",
      ),
    ).toBeInTheDocument();
  });

  it("renders single-row compare for ad-hoc-only run B (UJ-046)", () => {
    renderCompare(RUN_A, ADHOC_RUN);
    expect(
      compareRoot().getByTestId("eval-compare-row-adhoc"),
    ).toBeInTheDocument();
    expect(
      compareRoot().getByText(/Is the community center open on Sundays\?/),
    ).toBeInTheDocument();
    expect(
      compareRoot().queryByTestId("eval-compare-row-retrieval-miss"),
    ).not.toBeInTheDocument();
  });
});
