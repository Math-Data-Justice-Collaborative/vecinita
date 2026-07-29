import { expect, test, type Page, type Route } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

const LONG_TITLE =
  "Extremely long corpus document title that must clip with ellipsis so the actions column stays on screen for operators scanning the first page";
const LONG_URL =
  "https://example.org/path/to/a/very/long/resource/name/that/would/otherwise/blow/out/the/table/layout/and/push/actions";

const LONG_DOC = {
  document_id: "long-playwright-001",
  url: LONG_URL,
  title: LONG_TITLE,
  language: "en",
  tags: [
    { slug: "a", label: "A", source: "human" },
    { slug: "b", label: "B", source: "human" },
    { slug: "c", label: "C", source: "human" },
    { slug: "d", label: "D", source: "human" },
  ],
};

/**
 * UJ-051 / TC-155: Corpus density + truncation at ~1280×800 (EV-013 / #148).
 */
test.describe("Corpus table density and truncation", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await mockAuthenticatedAdmin(page);
    await page.route("**/internal/v1/documents**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [LONG_DOC],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      });
    });
  });

  test("clips long title/URL and keeps Actions reachable without page overflow", async ({
    page,
  }: {
    page: Page;
  }) => {
    await page.goto("/corpus");

    const title = page.getByTestId("corpus-title-long-playwright-001");
    await expect(title).toBeVisible();
    await expect(title).toHaveAttribute("title", LONG_TITLE);
    await expect(title).toHaveAttribute("aria-label", LONG_TITLE);

    const url = page.getByTestId("corpus-url-long-playwright-001");
    await expect(url).toHaveAttribute("href", LONG_URL);
    await expect(url).toHaveAttribute("title", LONG_URL);
    await expect(url).toHaveAttribute("aria-label", LONG_URL);

    const manage = page.getByRole("button", { name: /manage tags/i });
    await expect(manage).toBeVisible();
    const box = await manage.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x + box!.width).toBeLessThanOrEqual(1280);

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

    await expect(page.getByTestId("corpus-table-scroll")).toBeVisible();
  });
});
