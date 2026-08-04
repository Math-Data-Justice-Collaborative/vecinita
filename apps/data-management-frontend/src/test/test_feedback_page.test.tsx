import { cleanup, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as feedbackApi from "@/api/feedback";
import { ThemeProvider } from "@/components/ThemeProvider";
import { FeedbackPage } from "@/pages/FeedbackPage";

import { renderWithProviders } from "./renderWithProviders";

const MOCK_LIST = {
  items: [
    {
      id: "11111111-1111-4111-8111-111111111111",
      created_at: "2026-08-04T12:00:00Z",
      category: "suggestion",
      message: "Search felt truncated on mobile.",
      locale: "en",
    },
  ],
  page: 1,
  page_size: 20,
  total_count: 1,
};

function renderFeedback() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter>
        <FeedbackPage />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("Admin Feedback page (UJ-073 / F68)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("shows loading state while feedback loads", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    renderFeedback();
    expect(screen.getByTestId("feedback-admin-page")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders feedback rows from GET /admin/feedback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => MOCK_LIST,
      }),
    );
    renderFeedback();
    await waitFor(() => {
      expect(screen.getByTestId("feedback-row")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Search felt truncated on mobile."),
    ).toBeInTheDocument();
    expect(screen.getByText("suggestion")).toBeInTheDocument();
  });

  it("shows empty state when there are no rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          items: [],
          page: 1,
          page_size: 20,
          total_count: 0,
        }),
      }),
    );
    renderFeedback();
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    expect(screen.getByText(/no feedback/i)).toBeInTheDocument();
  });

  it("shows an error when the list request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      }),
    );
    renderFeedback();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("renders em dash when locale is null", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...MOCK_LIST,
          items: [
            {
              ...MOCK_LIST.items[0],
              locale: null,
            },
          ],
        }),
      }),
    );
    renderFeedback();
    await waitFor(() => {
      expect(screen.getByTestId("feedback-row")).toBeInTheDocument();
    });
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("ignores successful load after unmount", async () => {
    let resolveFetch: (value: Response) => void = () => undefined;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

    const { unmount } = renderFeedback();
    unmount();

    resolveFetch({
      ok: true,
      json: async () => MOCK_LIST,
    } as Response);

    await new Promise((resolve) => {
      setTimeout(resolve, 50);
    });
  });

  it("ignores load error after unmount", async () => {
    let rejectFetch: (reason?: unknown) => void = () => undefined;
    const pendingFetch = new Promise<Response>((_, reject) => {
      rejectFetch = reject;
    });
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

    const { unmount } = renderFeedback();
    unmount();

    rejectFetch(new Error("load failed after unmount"));

    await new Promise((resolve) => {
      setTimeout(resolve, 50);
    });
  });

  it("shows fallback message when load throws a non-Error", async () => {
    vi.spyOn(feedbackApi, "fetchFeedbackList").mockRejectedValue("boom");
    renderFeedback();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
