import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_EXPLORE_LAYOUT,
  loadEvalExploreLayout,
} from "./evalDashboardStorage";
import {
  DRILLDOWN_COLUMNS,
  loadEvalDrilldownLayout,
  saveEvalDrilldownLayout,
  toggleDrilldownColumn,
  type EvalDrilldownLayout,
} from "./evalDrilldownStorage";

const STORAGE_KEY = "vecinita.eval.drilldown.v1";

describe("evalDrilldownStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("defaults to question, answer, retrieval, and judge columns", () => {
    const layout = loadEvalDrilldownLayout();
    expect(layout.visibleColumns).toEqual([
      "question",
      "answer",
      "retrieval",
      "faithfulness",
      "answer_relevancy",
    ]);
    expect(layout.wrapCells).toBe(true);
  });

  it("loads persisted layout and filters unknown columns", () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        visibleColumns: ["question", "locale", "not-a-column"],
        wrapCells: false,
      }),
    );
    expect(loadEvalDrilldownLayout()).toEqual({
      visibleColumns: ["question", "locale"],
      wrapCells: false,
    });
  });

  it("falls back when persisted visible columns are empty or invalid JSON", () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ visibleColumns: [], wrapCells: true }),
    );
    expect(loadEvalDrilldownLayout().visibleColumns).toEqual([
      "question",
      "answer",
      "retrieval",
      "faithfulness",
      "answer_relevancy",
    ]);

    localStorage.setItem(STORAGE_KEY, "{bad");
    expect(loadEvalDrilldownLayout().wrapCells).toBe(true);
  });

  it("toggles columns without leaving the table empty", () => {
    const initial = loadEvalDrilldownLayout();
    const withoutAnswer = toggleDrilldownColumn(initial, "answer");
    expect(withoutAnswer.visibleColumns).not.toContain("answer");
    const restored = toggleDrilldownColumn(withoutAnswer, "answer");
    expect(restored.visibleColumns).toContain("answer");
  });

  it("keeps at least one column when toggling off the last visible column", () => {
    const onlyQuestion: EvalDrilldownLayout = {
      visibleColumns: ["question"],
      wrapCells: true,
    };
    expect(
      toggleDrilldownColumn(onlyQuestion, "question").visibleColumns,
    ).toEqual(["question"]);
  });

  it("saveEvalDrilldownLayout persists layout and degrades on quota errors", () => {
    const layout: EvalDrilldownLayout = {
      visibleColumns: ["question", "locale"],
      wrapCells: false,
    };
    saveEvalDrilldownLayout(layout);
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}")).toEqual(
      layout,
    );

    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => {
      saveEvalDrilldownLayout(layout);
    }).not.toThrow();
  });

  it("loads persisted layout with default wrapCells when omitted", () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ visibleColumns: ["question", "answer"] }),
    );
    expect(loadEvalDrilldownLayout().wrapCells).toBe(true);
  });

  it("loadEvalDrilldownLayout uses defaults when visibleColumns is omitted", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ wrapCells: false }));
    expect(loadEvalDrilldownLayout().visibleColumns).toEqual([
      "question",
      "answer",
      "retrieval",
      "faithfulness",
      "answer_relevancy",
    ]);
  });

  it("lists all supported drilldown columns", () => {
    expect(DRILLDOWN_COLUMNS).toContain("answer");
    expect(DRILLDOWN_COLUMNS).toContain("retrieved_urls");
  });

  it("does not collide with explore layout storage keys", () => {
    expect(loadEvalExploreLayout()).toEqual(DEFAULT_EXPLORE_LAYOUT);
  });
});
