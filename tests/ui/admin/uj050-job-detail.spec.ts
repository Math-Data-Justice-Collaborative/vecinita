import { expect, test } from "@playwright/test";

import {
  EVAL_JOB_ID,
  INGEST_JOB_ID,
  RETAG_DOC_ID,
  RETAG_JOB_ID,
  mockAuthenticatedAdmin,
} from "../helpers/mock-admin-api";

/** UJ-050 / RD-178: Jobs list → detail drill-down (+ failed Modal log fields). */
test.describe("Job detail drill-down (UJ-050)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("clicking ingest row opens /jobs/:id detail (TC-146)", async ({
    page,
  }) => {
    await page.goto("/jobs");

    const ingestRow = page
      .getByTestId("job-row")
      .filter({ hasText: INGEST_JOB_ID.slice(0, 8) });
    await expect(ingestRow).toBeVisible();
    await ingestRow.click();

    await expect(page).toHaveURL(
      new RegExp(`/jobs/${encodeURIComponent(INGEST_JOB_ID)}$`),
    );
    await expect(page.getByTestId("job-detail")).toBeVisible();
    await expect(page.getByText(/Completed/i)).toBeVisible();
    await expect(page.getByText(/https:\/\/example\.com\/page-a/)).toBeVisible();
  });

  test("failed retag detail shows document_id and Modal log affordances (TC-149)", async ({
    page,
  }) => {
    await page.goto(`/jobs/${encodeURIComponent(RETAG_JOB_ID)}`);

    await expect(page.getByTestId("job-detail")).toBeVisible();
    await expect(page.getByText(RETAG_DOC_ID)).toBeVisible();
    await expect(page.getByText("fc-retag-fail")).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Modal dashboard" }),
    ).toBeVisible();
  });

  test("eval detail links to evaluation drill-down (UJ-044 via UJ-050)", async ({
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
  });
});
