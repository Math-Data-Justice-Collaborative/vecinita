import { expect, test } from "@playwright/test";

import {
  mockAuthenticatedAdmin,
  mockAuthenticatedSuperAdmin,
} from "../helpers/mock-admin-api";

const DOWNLOAD_MODEL_ID = "qwen2.5:3b-instruct";
const DOWNLOAD_FAMILY = "qwen2.5";

/** UJ-048 / TC-137: super-admin model download tab + poll UX. */
test.describe("Playground model download (UJ-048)", () => {
  test("super-admin downloads model from models tab (TC-137)", async ({
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
      if (url.includes("/internal/v1/models/ollama/catalog/") && method === "GET") {
        const slug = decodeURIComponent(
          url.split("/internal/v1/models/ollama/catalog/")[1] ?? "",
        );
        const available = listCallCount >= 2;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            slug,
            tags: [
              { model_id: "qwen2.5:1.5b-instruct", available: true },
              { model_id: DOWNLOAD_MODEL_ID, available },
              { model_id: "qwen2.5:7b-instruct", available: false },
            ],
          }),
        });
        return;
      }
      if (url.includes("/internal/v1/models/ollama/catalog") && method === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            families: [{ slug: DOWNLOAD_FAMILY }],
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
              { model_id: "qwen2.5:7b-instruct", available: false },
            ],
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.goto("/evaluation?tab=models");
    await expect(page.getByTestId("evaluation-models-download")).toBeVisible();
    await page.getByTestId(`eval-models-family-${DOWNLOAD_FAMILY}`).locator("summary").click();
    await expect(
      page.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`),
    ).toBeVisible();
    await page.getByTestId(`eval-models-download-${DOWNLOAD_MODEL_ID}`).click();

    await expect(page.getByTestId("eval-models-download-status")).toContainText(
      /checking availability|comprobando/i,
    );
    await expect(page.getByTestId("eval-models-download-status")).toContainText(
      /available|disponible/i,
      { timeout: 15_000 },
    );
  });

  test("admin does not see model download tab (TC-136)", async ({ page }) => {
    await mockAuthenticatedAdmin(page);
    await page.goto("/evaluation?tab=playground");
    await expect(page.getByTestId("eval-playground-model-id")).toBeVisible();
    await expect(page.getByTestId("eval-tab-models")).toHaveCount(0);
    await expect(page.getByTestId("evaluation-models-download")).toHaveCount(0);
  });
});
