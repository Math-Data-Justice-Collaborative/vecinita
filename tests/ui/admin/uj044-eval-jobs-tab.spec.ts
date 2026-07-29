import { expect, test } from "@playwright/test";

import {
  EVAL_JOB_ID,
  mockAuthenticatedAdmin,
} from "../helpers/mock-admin-api";

/** UJ-044 / TC-124: eval runs on unified Jobs tab; drill-down via UJ-050 detail. */
test.describe("Eval jobs on Jobs tab (UJ-044)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("lists eval job with type badge and running status (TC-124)", async ({
    page,
  }) => {
    await page.goto("/jobs");

    const evalRow = page
      .getByTestId("job-row")
      .filter({ hasText: EVAL_JOB_ID.slice(0, 8) });
    await expect(evalRow).toBeVisible();
    await expect(evalRow).toContainText(/Eval/i);
    await expect(evalRow).toContainText(/Running/i);
  });

  test("clicking eval row opens detail then evaluation drill-down", async ({
    page,
  }) => {
    await page.goto("/jobs");

    const evalRow = page
      .getByTestId("job-row")
      .filter({ hasText: EVAL_JOB_ID.slice(0, 8) });
    await evalRow.click();

    await expect(page).toHaveURL(
      new RegExp(`/jobs/${encodeURIComponent(EVAL_JOB_ID)}$`),
    );
    await expect(page.getByTestId("job-detail")).toBeVisible();

    await page.getByRole("link", { name: "Open evaluation run" }).click();
    await expect(page).toHaveURL(
      new RegExp(
        `/evaluation\\?run=${encodeURIComponent(EVAL_JOB_ID)}.*tab=runs`,
      ),
    );
    await expect(page.getByTestId("evaluation-page")).toBeVisible();
    await expect(page.getByTestId("evaluation-history")).toBeVisible();
  });

  test("ingest jobs still render alongside eval rows", async ({ page }) => {
    await page.goto("/jobs");

    await expect(page.getByTestId("job-row").first()).toBeVisible();
    await expect(page.getByText(/Ingest/i).first()).toBeVisible();
    await expect(page.getByText(/Eval/i).first()).toBeVisible();
  });
});
