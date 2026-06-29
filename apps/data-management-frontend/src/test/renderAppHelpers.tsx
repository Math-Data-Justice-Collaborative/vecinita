import {
  render,
  screen,
  waitFor,
  type RenderResult,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import App from "@/App";
import { ThemeProvider } from "@/components/ThemeProvider";

import { installAuthenticatedSupabaseMock } from "./supabaseMock";
import { renderWithProviders } from "./renderWithProviders";

const { useMediaQueryMock } = vi.hoisted(() => ({
  useMediaQueryMock: vi.fn(() => true),
}));

vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: (query: string) => useMediaQueryMock(query),
}));

export { useMediaQueryMock };

/** Wait until ProtectedRoute finishes Supabase session bootstrap. */
export async function waitForAuthReady(): Promise<void> {
  await waitFor(() => {
    expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
  });
}

export function renderAppRoutes(initialRoute = "/dashboard"): RenderResult {
  installAuthenticatedSupabaseMock();
  return render(
    <LocaleProvider>
      <ThemeProvider>
        <MemoryRouter initialEntries={[initialRoute]}>
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

export async function renderAppRoutesReady(
  initialRoute = "/dashboard",
): Promise<RenderResult> {
  const result = renderAppRoutes(initialRoute);
  await waitForAuthReady();
  return result;
}

export function renderWithMemoryRouter(
  ui: ReactElement,
  initialRoute = "/",
): RenderResult {
  return renderWithProviders(
    <MemoryRouter initialEntries={[initialRoute]}>{ui}</MemoryRouter>,
  );
}
