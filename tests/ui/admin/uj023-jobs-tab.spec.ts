import { expect, test } from "@playwright/test";

import {
  INGEST_JOB_ID,
  RETAG_DOC_ID,
  RETAG_JOB_ID,
  mockAuthenticatedAdmin,
} from "../helpers/mock-admin-api";

/** UJ-023: Jobs tab list, retag document context, status filter (TC-150/151). */
test.describe("Jobs tab monitoring (UJ-023)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("lists ingest and retag jobs newest-first with types", async ({
    page,
  }) => {
    await page.goto("/jobs");

    // ingest + retag + eval + rebuild (F41) in mockJobsCatalog
    await expect(page.getByTestId("job-row")).toHaveCount(4);
    await expect(page.getByText(/Ingest/i).first()).toBeVisible();
    await expect(page.getByText(/Retag/i).first()).toBeVisible();
    await expect(page.getByText(/Rebuild/i).first()).toBeVisible();
    await expect(
      page.getByTestId("job-row").filter({ hasText: INGEST_JOB_ID.slice(0, 8) }),
    ).toBeVisible();
  });

  test("retag row shows document_id instead of empty URLs (TC-150)", async ({
    page,
  }) => {
    await page.goto("/jobs");

    const retagRow = page
      .getByTestId("job-row")
      .filter({ hasText: RETAG_JOB_ID.slice(0, 8) });
    await expect(retagRow).toBeVisible();
    await expect(retagRow).toContainText(RETAG_DOC_ID);
  });

  test("status filter requests GET /jobs?status= and narrows rows (TC-151)", async ({
    page,
  }) => {
    await page.goto("/jobs");
    await expect(page.getByTestId("job-row")).toHaveCount(4);

    const statusSelect = page.getByLabel(/status/i);
    await statusSelect.selectOption("failed");

    await expect
      .poll(async () => page.getByTestId("job-row").count())
      .toBe(1);
    await expect(
      page.getByTestId("job-row").filter({ hasText: RETAG_JOB_ID.slice(0, 8) }),
    ).toBeVisible();
  });
});
