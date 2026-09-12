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

  it("closes the drawer sidebar after navigating to Corpus on a narrow viewport", async () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 390,
    });
    const { container } = render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /toggle menu/i }));
    expect(container.querySelector(".sidebar-scrim")).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /^corpus$/i }));
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();
    expect(container.querySelector(".sidebar-scrim")).toBeNull();
  });

  it("browse-corpus CTA switches the shell to corpus browse", async () => {
    const sse =
      'data: {"token":"No matching sources were found."}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/ask/stream")) {
          const stream = new ReadableStream({
            start(controller) {
              controller.enqueue(new TextEncoder().encode(sse));
              controller.close();
            },
          });
          return Promise.resolve(
            new Response(stream, {
              status: 200,
              headers: { "Content-Type": "text/event-stream" },
            }),
          );
        }
        if (url.includes("/api/v1/warm")) {
          return Promise.resolve(
            new Response(JSON.stringify({ status: "warming" }), {
              status: 200,
            }),
          );
        }
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

    render(<App />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Where can I get food assistance?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    fireEvent.click(await screen.findByTestId("browse-corpus-cta"));
    expect(window.location.pathname).toBe("/corpus");
    expect(
      await screen.findByLabelText(/search title or url/i),
    ).toBeInTheDocument();
  });
});
