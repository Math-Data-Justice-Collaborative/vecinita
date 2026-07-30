import { expect, test } from "@playwright/test";

import {
  mockAuthenticatedAdmin,
  REBUILD_RUN_ID,
} from "../helpers/mock-admin-api";

/** UJ-054 / TC-169: Corpus RebuildPromoteForm confirm + promote API. */
test.describe("Corpus rebuild promote", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("admin confirms and promotes a shadow rebuild_run_id", async ({
    page,
  }) => {
    await page.goto("/corpus");

    await expect(page.getByTestId("rebuild-promote-form")).toBeVisible();
    await page.getByTestId("rebuild-promote-run-id").fill(REBUILD_RUN_ID);
    await page.getByTestId("rebuild-promote-confirm").check();
    await page.getByTestId("rebuild-promote-submit").click();

    await expect(page.getByTestId("rebuild-promote-result")).toContainText(
      "12",
    );
    await expect(page.getByTestId("rebuild-promote-result")).toContainText(
      REBUILD_RUN_ID,
    );
  });
});
