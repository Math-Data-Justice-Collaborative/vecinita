import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import { renderWithLocale } from "./renderWithLocale";

describe("UJ-073 Feedback page", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/tags")) {
          return new Response(JSON.stringify({ tags: [] }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/api/v1/feedback") && !url.includes("tags")) {
          return new Response(
            JSON.stringify({
              id: "11111111-1111-4111-8111-111111111111",
              created_at: "2026-08-04T12:00:00Z",
            }),
            {
              status: 201,
              headers: { "Content-Type": "application/json" },
            },
          );
        }
        return new Response("{}", { status: 404 });
      }),
    );
    window.history.pushState({}, "", "/");
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("navigates to Feedback and submits successfully", async () => {
    renderWithLocale(<App />);
    fireEvent.click(screen.getByTestId("nav-feedback"));
    expect(screen.getByTestId("feedback-page")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("feedback-message"), {
      target: { value: "Search felt truncated on mobile." },
    });
    fireEvent.click(screen.getByTestId("feedback-submit"));
    await waitFor(() => {
      expect(screen.getByTestId("feedback-success")).toBeInTheDocument();
    });
  });
});
