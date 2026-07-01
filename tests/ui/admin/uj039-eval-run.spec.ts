import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/** UJ-039/040: Evaluation run trigger ↔ history list ↔ drill-down table. */
test.describe("Evaluation run lifecycle", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("run button refreshes history and drill-down shows case rows", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=runs");

    await expect(page.getByTestId("evaluation-history")).toBeVisible();
    await page.getByTestId("evaluation-run-button").click();

    await expect(page.getByTestId("evaluation-drilldown")).toBeVisible();
    await expect(
      page.getByTestId("evaluation-drilldown"),
    ).toContainText(/food pantry hours/i);
  });

  test("selecting a history entry updates drill-down content", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=runs");

    const historyItem = page
      .getByTestId("evaluation-history")
      .getByRole("button")
      .first();
    await historyItem.click();

    await expect(page.getByTestId("evaluation-drilldown")).toBeVisible();
    await expect(
      page.getByTestId("evaluation-drilldown"),
    ).toContainText(/food pantry hours/i);
  });
});
