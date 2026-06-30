import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import App from "@/App";
import { ThemeProvider } from "@/components/ThemeProvider";

import { installViewerSupabaseMock } from "./supabaseMock";
import { useMediaQueryMock } from "./renderAppHelpers";

vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: (query: string) => useMediaQueryMock(query),
}));

function renderViewerApp(initialRoute: string) {
  installViewerSupabaseMock();
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

describe("Users nav viewer blocked (TC-089)", () => {
  beforeEach(() => {
    useMediaQueryMock.mockReturnValue(true);
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ jobs: [], users: [] }),
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("hides Users nav link for viewer operators", async () => {
    renderViewerApp("/dashboard");
    await waitFor(() => {
      expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("link", { name: /users/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /usuarios/i }),
    ).not.toBeInTheDocument();
  });

  it("redirects viewer away from /users", async () => {
    renderViewerApp("/users");
    await waitFor(() => {
      expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("users-page")).not.toBeInTheDocument();
  });
});
