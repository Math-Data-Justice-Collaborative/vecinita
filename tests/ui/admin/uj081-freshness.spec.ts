import { expect, test, type Page, type Route } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/**
 * UJ-081 / F76: Corpus freshness — stale badge, filter, Refresh now (TC-258 / TC-259).
 * [Corpus: feature-list.md §F76]
 * [Corpus: user-journeys.md §UJ-081]
 * [Spec: docs/test-plan.md §TC-258, TC-259]
 */

export const FRESHNESS_DOC_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd";

const STALE_DOC = {
  document_id: FRESHNESS_DOC_ID,
  url: "https://example.com/stale-source",
  title: "Stale Playwright Source",
  language: "en",
  tags: [],
  refresh_enabled: true,
  last_checked_at: "2026-06-01T00:00:00Z",
  stale: true,
};

async function mockFreshnessCorpus(page: Page): Promise<void> {
  let refreshEnabled = true;

  await page.route("**/internal/v1/documents**", async (route: Route) => {
    const request = route.request();
    const url = request.url();
    const method = request.method();

    if (url.includes(`/${FRESHNESS_DOC_ID}/refresh`) && method === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ job_id: "freshness-job-playwright-001" }),
      });
      return;
    }

    if (url.includes(`/${FRESHNESS_DOC_ID}/chunks`) && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
      return;
    }

    if (url.includes(`/${FRESHNESS_DOC_ID}/tags`) && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tags: [] }),
      });
      return;
    }

    if (url.includes(`/${FRESHNESS_DOC_ID}`) && method === "PATCH") {
      const body = JSON.parse(request.postData() ?? "{}") as {
        refresh_enabled?: boolean;
      };
      if (typeof body.refresh_enabled === "boolean") {
        refreshEnabled = body.refresh_enabled;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: FRESHNESS_DOC_ID,
          url: STALE_DOC.url,
          title: STALE_DOC.title,
          display_title: null,
          language: "en",
          refresh_enabled: refreshEnabled,
          last_checked_at: STALE_DOC.last_checked_at,
        }),
      });
      return;
    }

    if (method === "GET" && url.includes("/internal/v1/documents")) {
      const staleOnly = new URL(url).searchParams.get("stale") === "true";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: staleOnly || !staleOnly ? [STALE_DOC] : [],
          page: 1,
          page_size: 50,
          total: 1,
        }),
      });
      return;
    }

    await route.fallback();
  });
}

test.describe("Corpus freshness (UJ-081)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
    await mockFreshnessCorpus(page);
  });

  test("shows stale badge and last_checked; Refresh now queues job (TC-258/259)", async ({
    page,
  }) => {
    await page.goto("/corpus");

    await expect(
      page.getByTestId(`corpus-stale-badge-${FRESHNESS_DOC_ID}`),
    ).toBeVisible();
    await expect(
      page.getByTestId(`corpus-last-checked-${FRESHNESS_DOC_ID}`),
    ).toContainText("2026-06-01");

    const staleListPromise = page.waitForRequest(
      (req) =>
        req.method() === "GET" &&
        req.url().includes("/internal/v1/documents") &&
        req.url().includes("stale=true"),
    );
    await page.getByTestId("corpus-stale-filter").click();
    await staleListPromise;

    await page.getByRole("button", { name: /manage tags/i }).click();
    await expect(page.getByTestId("document-freshness-controls")).toBeVisible();
    await expect(page.getByTestId("document-refresh-now-btn")).toBeEnabled();

    const refreshPromise = page.waitForRequest(
      (req) =>
        req.method() === "POST" &&
        req.url().includes(`/documents/${FRESHNESS_DOC_ID}/refresh`),
    );
    await page.getByTestId("document-refresh-now-btn").click();
    await refreshPromise;
    await expect(page.getByRole("status")).toContainText(
      /freshness-job-playwright-001/i,
    );
  });

  test("disabling refresh_enabled PATCHes and disables Refresh now (TC-259)", async ({
    page,
  }) => {
    await page.goto("/corpus");
    await page.getByRole("button", { name: /manage tags/i }).click();

    const toggle = page.getByTestId("document-refresh-enabled-toggle");
    await expect(toggle).toBeChecked();

    const patchPromise = page.waitForRequest(
      (req) =>
        req.method() === "PATCH" &&
        req.url().includes(`/documents/${FRESHNESS_DOC_ID}`),
    );
    await toggle.click();
    const patch = await patchPromise;
    expect(JSON.parse(patch.postData() ?? "{}")).toEqual({
      refresh_enabled: false,
    });

    await expect(page.getByTestId("document-refresh-now-btn")).toBeDisabled();
  });
});
