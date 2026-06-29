import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AdminLayout } from "@/components/AdminLayout";
import { AuthProvider } from "@/auth/AuthContext";
import { ThemeProvider } from "@/components/ThemeProvider";
import { setSupabaseClientForTests } from "@/auth/supabaseClient";

describe("AdminLayout user menu", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("hides the user menu when no operator is signed in", async () => {
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
        onAuthStateChange: vi.fn().mockReturnValue({
          data: { subscription: { unsubscribe: vi.fn() } },
        }),
        signInWithPassword: vi.fn(),
        signOut: vi.fn(),
      },
    } as never);

    render(
      <LocaleProvider>
        <ThemeProvider>
          <AuthProvider>
            <MemoryRouter initialEntries={["/dashboard"]}>
              <Routes>
                <Route element={<AdminLayout />}>
                  <Route
                    path="/dashboard"
                    element={<div>Dashboard content</div>}
                  />
                </Route>
              </Routes>
            </MemoryRouter>
          </AuthProvider>
        </ThemeProvider>
      </LocaleProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("admin-user-menu")).not.toBeInTheDocument();
  });
});
