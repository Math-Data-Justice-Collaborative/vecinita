import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

const PLAYGROUND_RUN_ID = "00000000-0000-0000-0000-0000000000aa";
const RUN_A_ID = "00000000-0000-0000-0000-000000000099";
const RUN_B_ID = "00000000-0000-0000-0000-000000000088";

/** UJ-045: Playground configure + sandbox run. UJ-046: side-by-side compare. */
test.describe("Evaluation playground (UJ-045)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("playground tab renders two-column layout", async ({ page }) => {
    await page.goto("/evaluation?tab=playground");

    await expect(page.getByTestId("evaluation-playground")).toBeVisible();
    await expect(page.getByTestId("eval-playground-config-column")).toBeVisible();
    await expect(page.getByTestId("eval-playground-run-column")).toBeVisible();
    await expect(page.getByTestId("eval-playground-model-id")).toBeVisible();
  });

  test("Run evaluation opens playground tab (RD-129)", async ({ page }) => {
    await page.goto("/evaluation?tab=runs");

    await page.getByTestId("evaluation-run-button").click();

    await expect(page).toHaveURL(/tab=playground/);
    await expect(page.getByTestId("evaluation-playground")).toBeVisible();
  });

  test("golden batch run shows latest run id (TC-128)", async ({ page }) => {
    await page.goto("/evaluation?tab=playground");

    await page.getByTestId("eval-playground-mode-golden").click();
    await page.getByTestId("eval-playground-top-k").fill("11");
    await page
      .getByTestId("eval-playground-system-prompt")
      .fill("Sandbox-only system prompt for golden batch eval.");
    await page.getByTestId("eval-playground-run-button").click();

    await expect(page.getByTestId("eval-playground-last-run")).toContainText(
      PLAYGROUND_RUN_ID,
    );
  });

  test("ad-hoc question run enables button and shows run id (TC-129)", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=playground");

    await page.getByTestId("eval-playground-mode-adhoc").click();
    await expect(page.getByTestId("eval-playground-run-button")).toBeDisabled();

    const question = "What are the food pantry hours this week?";
    await page.getByTestId("eval-playground-adhoc-question").fill(question);
    await expect(page.getByTestId("eval-playground-run-button")).toBeEnabled();
    await page.getByTestId("eval-playground-run-button").click();

    await expect(page.getByTestId("eval-playground-last-run")).toContainText(
      PLAYGROUND_RUN_ID,
    );
  });
});

test.describe("Evaluation run compare (UJ-046)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("compare view shows metric deltas and per-question rows (TC-130)", async ({
    page,
  }) => {
    await page.goto("/evaluation?tab=runs");

    await page.getByTestId("eval-compare-toggle").click();
    await page.getByTestId("eval-compare-run-a-select").selectOption(RUN_A_ID);
    await page.getByTestId("eval-compare-run-b-select").selectOption(RUN_B_ID);

    await expect(page.getByTestId("evaluation-compare")).toBeVisible();
    await expect(page.getByTestId("eval-compare-run-a-label")).toContainText(
      RUN_A_ID,
    );
    await expect(page.getByTestId("eval-compare-run-b-label")).toContainText(
      RUN_B_ID,
    );
    await expect(
      page.getByTestId("eval-compare-metric-faithfulness"),
    ).toContainText("0.85");
    await expect(
      page.getByTestId("eval-compare-row-community-food-pantry"),
    ).toBeVisible();
    await expect(
      page.getByTestId("eval-compare-regression-community-food-pantry"),
    ).toBeVisible();
  });
});
