import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/**
 * UJ-041–043: EvaluationPage tabs coordinate URL, tab list, and panel content.
 */
test.describe("Evaluation dashboard tab interactions", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("dashboard tab shows charts and syncs URL query", async ({ page }) => {
    await page.goto("/evaluation?tab=runs");

    await page.getByTestId("eval-tab-dashboard").click();

    await expect(page).toHaveURL(/tab=dashboard/);
    await expect(page.getByTestId("evaluation-dashboard-tab")).toBeVisible();
    await expect(
      page.getByTestId("eval-chart-retrieval_relevance"),
    ).toBeVisible();
  });

  test("dashboard supports scatter chart and time-range presets (TC-125)", async ({
    page,
  }) => {
    await page.clock.install({ time: new Date("2026-07-02T18:00:00Z") });
    await page.goto("/evaluation?tab=dashboard");

    await expect(page.getByTestId("evaluation-dashboard-tab")).toBeVisible();
    for (const preset of ["1D", "7D", "10D", "1M", "1Y", "custom"] as const) {
      await expect(page.getByTestId(`eval-time-preset-${preset}`)).toBeVisible();
    }

    await page.getByTestId("eval-time-preset-1D").click();
    await page.getByTestId("eval-chart-type-toggle").click();
    await page.getByTestId("eval-chart-type-toggle").click();

    await expect(page.getByTestId("eval-chart-type-toggle")).toHaveText(
      /Scatter chart/i,
    );
    await expect(
      page.getByTestId("eval-chart-retrieval_relevance"),
    ).toBeVisible();

    const stored = await page.evaluate(() =>
      localStorage.getItem("vecinita.eval.dashboard.v1"),
    );
    expect(stored).toContain('"chartType":"scatter"');
    expect(stored).toContain('"timeRangePreset":"1D"');
  });

  test("dashboard custom date range shows empty state (TC-126)", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=dashboard");

    await expect(page.getByTestId("evaluation-dashboard-tab")).toBeVisible();
    await page.getByTestId("eval-time-preset-custom").click();
    await page.getByTestId("eval-custom-range-start").fill("2025-01-01");
    await page.getByTestId("eval-custom-range-end").fill("2025-01-31");

    await expect(page.getByTestId("eval-custom-range-empty")).toBeVisible();
    await expect(page.getByTestId("eval-custom-range-empty")).toContainText(
      /No runs in the selected custom date range/i,
    );
    await expect(
      page.getByTestId("eval-chart-retrieval_relevance"),
    ).not.toBeVisible();
  });

  test("explore tab pivot row axis persists to localStorage", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=explore");

    await expect(page.getByTestId("evaluation-explore-tab")).toBeVisible();
    await page.getByTestId("eval-pivot-row-axis").selectOption("case_id");

    const stored = await page.evaluate(() =>
      localStorage.getItem("vecinita.eval.explore.v1"),
    );
    expect(stored).toContain("case_id");
    await expect(page.getByTestId("eval-pivot-table")).toBeVisible();
  });

  test("criteria tab lists items and accepts new criterion form input", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=criteria");

    await expect(page.getByTestId("evaluation-criteria-tab")).toBeVisible();
    await expect(page.getByTestId("eval-criterion-tone-friendly")).toBeVisible();

    await page.getByTestId("eval-criterion-slug").fill("browser-criterion");
    await page.getByTestId("eval-criterion-label").fill("Browser criterion");
    await page.getByTestId("eval-criterion-rubric").fill("Must cite sources");

    await expect(page.getByTestId("eval-criterion-create")).toBeEnabled();
  });
});
