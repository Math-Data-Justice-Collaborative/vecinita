import { describe, expect, it } from "vitest";

import {
  DEFAULT_EXPLORE_LAYOUT,
  loadEvalExploreLayout,
} from "./evalDashboardStorage";
import {
  DRILLDOWN_COLUMNS,
  loadEvalDrilldownLayout,
  toggleDrilldownColumn,
} from "./evalDrilldownStorage";

describe("evalDrilldownStorage", () => {
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

  it("toggles columns without leaving the table empty", () => {
    const initial = loadEvalDrilldownLayout();
    const withoutAnswer = toggleDrilldownColumn(initial, "answer");
    expect(withoutAnswer.visibleColumns).not.toContain("answer");
    const restored = toggleDrilldownColumn(withoutAnswer, "answer");
    expect(restored.visibleColumns).toContain("answer");
  });

  it("lists all supported drilldown columns", () => {
    expect(DRILLDOWN_COLUMNS).toContain("answer");
    expect(DRILLDOWN_COLUMNS).toContain("retrieved_urls");
  });

  it("does not collide with explore layout storage keys", () => {
    expect(loadEvalExploreLayout()).toEqual(DEFAULT_EXPLORE_LAYOUT);
  });
});
