import type { Page } from "@playwright/test";

/**
 * Stub Supabase Auth HTTP so the login shell renders without a live project.
 * Fresh browser context has no persisted session; these routes cover refresh probes.
 */
export async function mockSupabaseAuth(page: Page): Promise<void> {
  await page.route(/\/auth\/v1\//, async (route) => {
    const url = route.request().url();
    if (url.includes("token") && route.request().method() === "POST") {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          error: "invalid_grant",
          error_description: "playwright stub",
        }),
      });
      return;
    }
    if (url.includes("/user") && route.request().method() === "GET") {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          message: "JWT expired",
          error: "invalid_token",
        }),
      });
      return;
    }
    await route.continue();
  });
}
