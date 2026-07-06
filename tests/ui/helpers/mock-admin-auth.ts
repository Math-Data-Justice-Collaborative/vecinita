import type { Page } from "@playwright/test";

const ADMIN_SESSION = {
  access_token: "playwright-admin-jwt",
  refresh_token: "playwright-admin-refresh",
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  token_type: "bearer",
  user: {
    id: "11111111-1111-1111-1111-111111111111",
    aud: "authenticated",
    role: "authenticated",
    email: "admin@vecinita.admin",
    app_metadata: { role: "admin" },
    user_metadata: {},
  },
};

const VIEWER_SESSION = {
  access_token: "playwright-viewer-jwt",
  refresh_token: "playwright-viewer-refresh",
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  token_type: "bearer",
  user: {
    id: "22222222-2222-2222-2222-222222222222",
    aud: "authenticated",
    role: "authenticated",
    email: "viewer@vecinita.admin",
    app_metadata: { role: "viewer" },
    user_metadata: {},
  },
};

const SUPER_ADMIN_SESSION = {
  access_token: "playwright-super-admin-jwt",
  refresh_token: "playwright-super-admin-refresh",
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  token_type: "bearer",
  user: {
    id: "44444444-4444-4444-4444-444444444444",
    aud: "authenticated",
    role: "authenticated",
    email: "superadmin@vecinita.admin",
    app_metadata: { role: "super-admin" },
    user_metadata: {},
  },
};

/**
 * Seed Supabase browser session so ProtectedRoute renders admin shell.
 * Build uses VITE_SUPABASE_URL=https://placeholder.supabase.co → storage key below.
 */
export async function seedAdminSession(page: Page): Promise<void> {
  await page.addInitScript((session) => {
    localStorage.setItem("sb-placeholder-auth-token", JSON.stringify(session));
  }, ADMIN_SESSION);

  await page.route(/\/auth\/v1\//, async (route) => {
    const url = route.request().url();
    if (url.includes("/user") && route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(ADMIN_SESSION.user),
      });
      return;
    }
    await route.continue();
  });
}

export async function seedViewerSession(page: Page): Promise<void> {
  await page.addInitScript((session) => {
    localStorage.setItem("sb-placeholder-auth-token", JSON.stringify(session));
  }, VIEWER_SESSION);

  await page.route(/\/auth\/v1\//, async (route) => {
    const url = route.request().url();
    if (url.includes("/user") && route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(VIEWER_SESSION.user),
      });
      return;
    }
    await route.continue();
  });
}

/** Seed Supabase browser session with super-admin app_metadata role (UJ-048). */
export async function seedSuperAdminSession(page: Page): Promise<void> {
  await page.addInitScript((session) => {
    localStorage.setItem("sb-placeholder-auth-token", JSON.stringify(session));
  }, SUPER_ADMIN_SESSION);

  await page.route(/\/auth\/v1\//, async (route) => {
    const url = route.request().url();
    if (url.includes("/user") && route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(SUPER_ADMIN_SESSION.user),
      });
      return;
    }
    await route.continue();
  });
}
