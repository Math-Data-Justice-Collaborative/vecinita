import {
  act,
  cleanup,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "../components/ChatPanel";
import * as browse from "../api/browse";
import { renderWithLocale } from "./renderWithLocale";

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
      const response =
        handlers.tags ??
        new Response(JSON.stringify({ tags: [] }), { status: 200 });
      return Promise.resolve(
        typeof response === "function" ? response() : response,
      );
    }
    if (url.includes("/api/v1/ask/stream")) {
      const response = handlers.stream;
      if (!response) {
        return Promise.reject(new Error("Unexpected ask/stream fetch"));
      }
      return Promise.resolve(
        typeof response === "function" ? response() : response,
      );
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

    renderWithLocale(<ChatPanel />);
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
        body: JSON.stringify({
          question: "When is the food pantry open?",
          language: "en",
        }),
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
      .fn<() => Promise<Response>>()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockImplementation(async () => sseResponse(okSse));

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/tags")) {
          return Promise.resolve(
            new Response(JSON.stringify({ tags: [] }), { status: 200 }),
          );
        }
        if (url.includes("/api/v1/ask/stream")) {
          return streamFetch();
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    renderWithLocale(<ChatPanel />);
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

    renderWithLocale(<ChatPanel />);
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

  it("completes when the stream has sources and done but no tokens", async () => {
    const sse = 'data: {"sources":[]}\n\n' + 'data: {"done":true}\n\n';
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(sse),
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Silent?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(screen.getAllByTestId("message")).toHaveLength(2);
    });
    const assistant = screen.getAllByTestId("message")[1];
    expect(assistant.querySelector(".message-content")).toHaveTextContent("");
  });

  it("ignores unrecognized stream events", async () => {
    const sse =
      'data: {"token":"Hi"}\n\n' +
      'data: {"unexpected":true}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(sse),
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Hello?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(screen.getByText(/^Hi$/)).toBeInTheDocument();
    });
  });

  it("ignores whitespace-only questions", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(
          'data: {"token":"No"}\n\n' +
            'data: {"sources":[]}\n\n' +
            'data: {"done":true}\n\n',
        ),
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "   " },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/ask/stream"),
      expect.anything(),
    );
  });

  it("shows Asking label while a stream is in flight", async () => {
    let releaseStream: ((value: Response) => void) | undefined;
    const pendingStream = new Promise<Response>((resolve) => {
      releaseStream = resolve;
    });

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/tags")) {
          return Promise.resolve(
            new Response(JSON.stringify({ tags: [] }), { status: 200 }),
          );
        }
        if (url.includes("/api/v1/ask/stream")) {
          return pendingStream;
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Slow?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(
      await screen.findByRole("button", { name: /asking/i }),
    ).toBeDisabled();

    releaseStream?.(
      sseResponse(
        'data: {"token":"Done"}\n\n' +
          'data: {"sources":[]}\n\n' +
          'data: {"done":true}\n\n',
      ),
    );
  });

  it("ignores a second submit while the first ask is still loading", async () => {
    let releaseStream: ((value: Response) => void) | undefined;
    const pendingStream = new Promise<Response>((resolve) => {
      releaseStream = resolve;
    });
    const streamFetch = vi.fn(() => pendingStream);

    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/tags")) {
          return Promise.resolve(
            new Response(JSON.stringify({ tags: [] }), { status: 200 }),
          );
        }
        if (url.includes("/api/v1/ask/stream")) {
          return streamFetch();
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "First?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Second?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /asking/i }));

    expect(streamFetch).toHaveBeenCalledTimes(1);
    releaseStream?.(
      sseResponse(
        'data: {"token":"Done"}\n\n' +
          'data: {"sources":[]}\n\n' +
          'data: {"done":true}\n\n',
      ),
    );
  });

  it("does not update tag facets after unmount", async () => {
    let resolveTags: ((value: { tags: browse.TagFacet[] }) => void) | undefined;
    vi.spyOn(browse, "fetchTags").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTags = resolve;
        }),
    );

    const { unmount } = renderWithLocale(<ChatPanel />);
    unmount();
    resolveTags?.({ tags: [] });
  });

  it("ignores empty submissions and shows tag filter chips", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        tags: new Response(
          JSON.stringify({
            tags: [
              {
                slug: "housing",
                label: "Housing",
                language: "en",
                document_count: 1,
              },
            ],
          }),
          { status: 200 },
        ),
      }),
    );

    renderWithLocale(<ChatPanel />);
    expect(await screen.findByTestId("tag-filter-chips")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
    expect(screen.queryAllByTestId("message")).toHaveLength(0);
  });

  it("includes selected tags in the ask request and deselects chips", async () => {
    const sse =
      'data: {"token":"Ok"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        tags: new Response(
          JSON.stringify({
            tags: [
              {
                slug: "housing",
                label: "Housing",
                language: "en",
                document_count: 1,
              },
            ],
          }),
          { status: 200 },
        ),
        stream: sseResponse(sse),
      }),
    );

    renderWithLocale(<ChatPanel />);
    const chip = await screen.findByRole("button", { name: "Housing" });
    fireEvent.click(chip);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Need housing help?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/ask/stream",
        expect.objectContaining({
          body: JSON.stringify({
            question: "Need housing help?",
            language: "en",
            tags: ["housing"],
          }),
        }),
      );
    });

    fireEvent.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "false");
  });

  it("surfaces localized errors for non-transient ask failures", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: new Response("Forbidden", { status: 403 }),
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "Hello?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /not authorized/i,
    );
  });

  it("continues when tag facets fail to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === "string" ? input : input.toString();
        if (url.includes("/api/v1/tags")) {
          return Promise.reject(new Error("Tags failed (500)"));
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    renderWithLocale(<ChatPanel />);
    expect(await screen.findByText(/ask a question/i)).toBeInTheDocument();
    expect(screen.queryByTestId("tag-filter-chips")).not.toBeInTheDocument();
  });
});
