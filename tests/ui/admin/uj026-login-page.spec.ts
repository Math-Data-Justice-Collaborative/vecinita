import { expect, test } from "@playwright/test";

import { mockSupabaseAuth } from "../helpers/mock-supabase-auth";

/** UJ-026 (browser): Admin login page renders for unauthenticated visitors. */
test.describe("Admin login page", () => {
  test.beforeEach(async ({ page }) => {
    await mockSupabaseAuth(page);
  });

  test("shows invitation-only sign-in form", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByTestId("login-form")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /sign in/i }),
    ).toBeVisible();
    await expect(
      page.getByText(/invitation-only access for corpus operators/i),
    ).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });
});
