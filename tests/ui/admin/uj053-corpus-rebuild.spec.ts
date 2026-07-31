import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/** UJ-053 / TC-167: Corpus RebuildForm mode/force/dry_run enqueue. */
test.describe("Corpus rebuild enqueue", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("admin sets mode/force/dry-run and sees rebuild job status", async ({
    page,
  }) => {
    await page.goto("/corpus");

    await expect(page.getByTestId("rebuild-form")).toBeVisible();
    await page.getByTestId("rebuild-mode").selectOption("rechunk");
    await page.getByTestId("rebuild-force").check();
    await page.getByTestId("rebuild-dry-run").check();
    await page.getByTestId("rebuild-submit").click();

    await expect(page.getByTestId("rebuild-job-status")).toContainText(
      /pending|77777777/i,
    );

    await page.goto("/jobs");
    await expect(page.getByText(/Rebuild/i).first()).toBeVisible();
  });
});
