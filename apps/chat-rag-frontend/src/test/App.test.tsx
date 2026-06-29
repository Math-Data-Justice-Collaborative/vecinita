import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";

describe("App navigation", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.replaceState({}, "", "/");
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/documents")) {
          return Promise.resolve(
            new Response(
              JSON.stringify({
                items: [],
                page: 1,
                page_size: 20,
                total: 0,
              }),
              { status: 200 },
            ),
          );
        }
        return Promise.resolve(
          new Response(JSON.stringify({ tags: [] }), { status: 200 }),
        );
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    window.history.replaceState({}, "", "/");
  });

  it("switches between chat and corpus views", async () => {
    render(<App />);
    expect(screen.getByLabelText(/your question/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^corpus$/i }));
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /back to chat/i }));
    expect(screen.getByLabelText(/your question/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^chat$/i }));
    expect(screen.getByLabelText(/your question/i)).toBeInTheDocument();
  });

  it("shows corpus browse when pathname ends with /corpus", async () => {
    window.history.replaceState({}, "", "/app/corpus");
    render(<App />);
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();
  });

  it("collapses the sidebar via the scrim and re-opens it via the header toggle", () => {
    const { container } = render(<App />);

    const scrim = container.querySelector(".sidebar-scrim");
    expect(scrim).not.toBeNull();
    fireEvent.click(scrim as Element);
    expect(container.querySelector(".sidebar-scrim")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /toggle menu/i }));
    expect(container.querySelector(".sidebar-scrim")).not.toBeNull();
  });
});
