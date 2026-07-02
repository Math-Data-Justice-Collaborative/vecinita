import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { type EvalRunDetailApi } from "@/api/admin";

import { EvaluationDrilldownTable } from "./EvaluationDrilldownTable";

const SAMPLE_ITEMS: EvalRunDetailApi["items"] = [
  {
    case_id: "community-food-pantry",
    locale: "en",
    question: "When are food pantry hours updated?",
    expected_doc_url: "fixture://corpus/en/community-resources.md",
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
    locale: "es",
    question: "Where is the wrong document?",
    expected_doc_url: null,
    retrieved_urls: [],
    answer: null,
    metrics: {
      retrieval_pass: false,
      faithfulness: 0.4,
      answer_relevancy: 0.3,
      latency_ms: 900,
    },
  },
];

function renderTable(items: EvalRunDetailApi["items"] = SAMPLE_ITEMS) {
  return render(
    <LocaleProvider>
      <EvaluationDrilldownTable items={items} />
    </LocaleProvider>,
  );
}

function drilldownRoot() {
  return within(screen.getByTestId("evaluation-drilldown"));
}

describe("EvaluationDrilldownTable", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders default columns and row content", () => {
    renderTable();
    expect(drilldownRoot().getByText("When are food pantry hours updated?")).toBeInTheDocument();
    expect(drilldownRoot().getByText("0.85")).toBeInTheDocument();
    expect(drilldownRoot().getByText("Fail")).toBeInTheDocument();
  });

  it("opens the column picker and toggles optional columns", () => {
    renderTable();
    const root = drilldownRoot();
    fireEvent.click(root.getByTestId("eval-drilldown-columns-toggle"));
    expect(root.getByTestId("eval-drilldown-column-picker")).toBeInTheDocument();

    fireEvent.click(root.getByTestId("eval-drilldown-col-locale"));
    expect(root.getByText("es")).toBeInTheDocument();

    fireEvent.click(root.getByTestId("eval-drilldown-col-case_id"));
    expect(root.getByText("retrieval-miss")).toBeInTheDocument();

    fireEvent.click(root.getByTestId("eval-drilldown-col-retrieved_urls"));
    expect(root.getByTestId("eval-drilldown-col-retrieved_urls")).toHaveAttribute(
      "aria-checked",
      "true",
    );

    fireEvent.click(root.getByTestId("eval-drilldown-col-expected_doc_url"));
    expect(root.getByTestId("eval-drilldown-col-expected_doc_url")).toHaveAttribute(
      "aria-checked",
      "true",
    );

    fireEvent.click(root.getByTestId("eval-drilldown-col-latency_ms"));
    expect(root.getByText("3100 ms")).toBeInTheDocument();
  });

  it("toggles wrap cells off", () => {
    renderTable();
    const wrapToggle = drilldownRoot().getByTestId("eval-drilldown-wrap-toggle");
    expect(wrapToggle).toBeChecked();
    fireEvent.click(wrapToggle);
    expect(wrapToggle).not.toBeChecked();
  });

  it("highlights low judge scores and missing values", () => {
    renderTable();
    const root = drilldownRoot();
    expect(root.getAllByText("0.40")[0]).toHaveClass("text-destructive");
    expect(root.getAllByText("0.30")[0]).toHaveClass("text-destructive");
    expect(root.getAllByText("—").length).toBeGreaterThan(0);
  });
});
