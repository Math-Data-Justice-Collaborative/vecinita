import { render, screen, waitFor } from "@testing-library/react";
import { expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LocaleProvider } from "vecinita-frontend-ui";

import App from "@/App";
import { AuthProvider } from "@/auth/AuthContext";
import { setSupabaseClientForTests } from "@/auth/supabaseClient";
import { ThemeProvider } from "@/components/ThemeProvider";

export const mockSignOut = vi.fn().mockResolvedValue({ error: null });

export function renderSignedInApp(initialPath = "/dashboard") {
  setSupabaseClientForTests({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            access_token: "jwt",
            user: {
              id: "admin-1",
              email: "admin@vecinita.admin",
              app_metadata: { role: "admin" },
            },
          },
        },
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn(),
      signOut: mockSignOut,
    },
  } as never);

  return render(
    <LocaleProvider>
      <ThemeProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route path="/*" element={<App />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>
    </LocaleProvider>,
  );
}

export async function waitForAdminNav() {
  await waitFor(() => {
    expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
  });
}
