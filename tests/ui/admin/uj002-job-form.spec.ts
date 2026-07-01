import { expect, test } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/** UJ-002: Corpus JobForm ↔ jobs API ↔ status panel on Corpus page. */
test.describe("Ingest job form", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
  });

  test("submits URLs and shows completed job status", async ({ page }) => {
    await page.goto("/corpus");

    await page.getByLabel(/urls/i).fill("https://example.com/page-a\nhttps://example.com/page-b");
    await page.getByRole("button", { name: /submit ingest job/i }).click();

    await expect(page.getByTestId("job-status")).toContainText(/completed/i);
  });
});
