import { expect, test, type Page, type Route } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

const TREE_PAYLOAD = {
  roots: [
    {
      id: "domain:tree.example.com",
      kind: "domain",
      label: "tree.example.com",
      counts: { documents: 2 },
      children: [
        {
          id: "path:tree.example.com/guides",
          kind: "path",
          label: "guides",
          children: [
            {
              id: "doc-a",
              kind: "document",
              label: "a.html",
              url: "https://tree.example.com/guides/a.html",
              status: "completed",
              source_domain: "tree.example.com",
              source_path: "/guides",
            },
            {
              id: "doc-b",
              kind: "document",
              label: "b.html",
              url: "https://tree.example.com/guides/b.html",
              status: "completed",
              source_domain: "tree.example.com",
              source_path: "/guides",
            },
          ],
        },
      ],
    },
  ],
};

const FLAT_PAYLOAD = {
  items: [
    {
      document_id: "doc-a",
      url: "https://tree.example.com/guides/a.html",
      title: "Guide A",
      language: "en",
      tags: [],
    },
  ],
  page: 1,
  page_size: 50,
  total: 1,
};

/**
 * UJ-066 / TC-207: Corpus tree ↔ flat toggle + nesting + bulk from tree (F61).
 */
test.describe("Corpus tree nesting", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
    await page.route("**/internal/v1/corpus/tree**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TREE_PAYLOAD),
      });
    });
    await page.route("**/internal/v1/documents**", async (route: Route) => {
      if (route.request().url().includes("/corpus/tree")) {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(FLAT_PAYLOAD),
      });
    });
  });

  test("toggles tree/flat, expands nesting, and selects docs for bulk (TC-207)", async ({
    page,
  }: {
    page: Page;
  }) => {
    await page.goto("/corpus");

    await expect(page.getByTestId("corpus-view-flat")).toBeVisible();
    await expect(page.getByText("Guide A")).toBeVisible();

    await page.getByTestId("corpus-view-tree").click();
    await expect(page.getByRole("tree")).toBeVisible();
    await expect(page.getByText("tree.example.com")).toBeVisible();

    await page.getByRole("button", { name: /expand tree\.example\.com/i }).click();
    await expect(page.getByText("guides")).toBeVisible();
    await page.getByRole("button", { name: /expand guides/i }).click();
    await expect(page.getByText("a.html", { exact: true })).toBeVisible();

    await page.getByRole("checkbox", { name: /select a\.html/i }).click();
    await expect(page.getByTestId("bulk-toolbar")).toBeVisible();
    await expect(page.getByTestId("bulk-tag-btn")).toBeVisible();

    await page.getByTestId("corpus-view-flat").click();
    await expect(page.getByText("Guide A")).toBeVisible();
  });
});
