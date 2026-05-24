import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "../components/ChatPanel";

function sseResponse(body: string): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

function mockFetchRouter(handlers: {
  tags?: Response | (() => Response);
  stream?: Response | (() => Response);
}) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/api/v1/tags")) {
      const response = handlers.tags ?? new Response(JSON.stringify({ tags: [] }), { status: 200 });
      return Promise.resolve(typeof response === "function" ? response() : response);
    }
    if (url.includes("/api/v1/ask/stream")) {
      const response = handlers.stream;
      if (!response) {
        return Promise.reject(new Error("Unexpected ask/stream fetch"));
      }
      return Promise.resolve(typeof response === "function" ? response() : response);
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });
}

describe("ChatPanel", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("streams answer tokens and shows source citations", async () => {
    const sse =
      'data: {"token":"The "}\n\n' +
      'data: {"token":"pantry "}\n\n' +
      'data: {"sources":[{"chunk_id":"c1","document_id":"d1","title":"Food pantry","url":"https://example.com","score":0.9}]}\n\n' +
      'data: {"done":true}\n\n';

    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(sse),
      }),
    );

    render(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "When is the food pantry open?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("source-list")).toBeInTheDocument();
    });

    expect(screen.getByText(/The pantry/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /food pantry/i })).toHaveAttribute(
      "href",
      "https://example.com",
    );
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/ask/stream",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "When is the food pantry open?" }),
      }),
    );
  });

  it("shows warm-up status when the first ask attempt fails transiently", async () => {
    vi.useFakeTimers();

    const okSse =
      'data: {"token":"Hi"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const streamFetch = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockImplementation(async () => sseResponse(okSse));

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/tags")) {
          return Promise.resolve(new Response(JSON.stringify({ tags: [] }), { status: 200 }));
        }
        if (url.includes("/api/v1/ask/stream")) {
          return streamFetch();
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    render(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Hello?" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
      await Promise.resolve();
    });

    expect(screen.getByRole("status")).toHaveTextContent(/starting up/i);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(screen.getByText(/^Hi$/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("keeps history client-side and clears on demand", async () => {
    const sse =
      'data: {"token":"Hi"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(sse),
      }),
    );

    render(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Hello?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(screen.getAllByTestId("message")).toHaveLength(2);
    });

    fireEvent.click(screen.getByRole("button", { name: /clear history/i }));
    expect(screen.getByText(/ask a question/i)).toBeInTheDocument();
  });
});
