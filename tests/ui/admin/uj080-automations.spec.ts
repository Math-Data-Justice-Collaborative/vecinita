import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/**
 * UJ-080 / F75: Automations panel — nav, enable/disable, run history (TC-252 / TC-255).
 * [Corpus: feature-list.md §F75]
 * [Corpus: user-journeys.md §UJ-080]
 * [Spec: docs/test-plan.md §TC-252, TC-255]
 */
test.describe("Automations panel (UJ-080)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("nav opens Automations with enable toggle and run history", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    await page.getByRole("link", { name: /automations/i }).click();
    await expect(page).toHaveURL(/\/automations/);
    await expect(page.getByTestId("automations-admin-page")).toBeVisible();

    const toggle = page.getByTestId("automations-enabled-toggle");
    await expect(toggle).toBeChecked();
    await expect(page.getByTestId("automations-enabled-status")).toContainText(
      /enabled/i,
    );
    await expect(page.getByTestId("automations-kill-switch")).toContainText(
      /off/i,
    );

    const row = page.getByTestId("automation-run-row");
    await expect(row).toHaveCount(1);
    await expect(row).toContainText("automation_catchup");
    await expect(row).toContainText("completed");
    await expect(row).toContainText("aaaaaaaa"); // RETAG_DOC_ID prefix in mock run
  });

  test("disabling automations PATCHes config and shows disabled (TC-252)", async ({
    page,
  }) => {
    await page.goto("/automations");

    const toggle = page.getByTestId("automations-enabled-toggle");
    await expect(toggle).toBeChecked();

    const patchPromise = page.waitForRequest(
      (req) =>
        req.method() === "PATCH" &&
        req.url().includes("/internal/v1/automations/config"),
    );
    await toggle.click();
    const patch = await patchPromise;
    expect(JSON.parse(patch.postData() ?? "{}")).toEqual({ enabled: false });

    await expect(toggle).not.toBeChecked();
    await expect(page.getByTestId("automations-enabled-status")).toContainText(
      /disabled/i,
    );
  });
});
