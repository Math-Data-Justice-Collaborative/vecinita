import { expect, test } from "@playwright/test";

import {
  mockAuthenticatedAdmin,
  mockAuthenticatedSuperAdmin,
} from "../helpers/mock-admin-api";

const DOWNLOAD_MODEL_ID = "qwen2.5:3b-instruct";

/** UJ-048 / TC-137: super-admin model download panel + poll UX. */
test.describe("Playground model download (UJ-048)", () => {
  test("super-admin downloads model and picker updates (TC-137)", async ({
    page,
  }) => {
    let listCallCount = 0;
    await mockAuthenticatedSuperAdmin(page);
    await page.route("**/internal/v1/models/ollama**", async (route) => {
      const url = route.request().url();
      const method = route.request().method();
      if (url.includes("/pull") && method === "POST") {
        await route.fulfill({
          status: 202,
          contentType: "application/json",
          body: JSON.stringify({
            job_id: "00000000-0000-0000-0000-0000000000dd",
            model_id: DOWNLOAD_MODEL_ID,
            status: "pulling",
          }),
        });
        return;
      }
      if (method === "GET") {
        listCallCount += 1;
        const available = listCallCount >= 2;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [
              { model_id: "qwen2.5:1.5b-instruct", available: true },
              { model_id: DOWNLOAD_MODEL_ID, available },
            ],
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/evaluation?tab=playground");
    await expect(page.getByTestId("eval-playground-download-card")).toBeVisible();
    await page.getByTestId("eval-playground-download-model-id").fill(DOWNLOAD_MODEL_ID);
    await page.getByTestId("eval-playground-download-button").click();

    await expect(page.getByTestId("eval-playground-download-status")).toContainText(
      /checking availability|comprobando/i,
    );
    await expect(page.getByTestId("eval-playground-download-status")).toContainText(
      /available|disponible/i,
      { timeout: 15_000 },
    );
    await expect(page.getByTestId("eval-playground-model-id")).toHaveValue(
      DOWNLOAD_MODEL_ID,
    );
  });

  test("admin does not see download panel (TC-136)", async ({ page }) => {
    await mockAuthenticatedAdmin(page);
    await page.goto("/evaluation?tab=playground");
    await expect(page.getByTestId("eval-playground-model-id")).toBeVisible();
    await expect(page.getByTestId("eval-playground-download-card")).toHaveCount(0);
  });
});
