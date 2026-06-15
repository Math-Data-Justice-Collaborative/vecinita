import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { DocumentAdmin } from "@/components/DocumentAdmin";

const DOC = {
  document_id: "doc-aaa",
  url: "https://example.com/guide",
  title: "Housing Guide",
  language: "en",
  tags: [],
};

function renderAdmin() {
  const onClose = vi.fn();
  renderWithProviders(
    <ThemeProvider>
      <DocumentAdmin document={DOC} onClose={onClose} />
    </ThemeProvider>,
  );
  return { onClose };
}

function jsonOk(body: unknown) {
  return { ok: true, json: async () => body };
}

describe("DocumentAdmin", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          jsonOk([
            {
              chunk_id: "chunk-1",
              chunk_index: 0,
              text: "Chunk body text",
              tags: [{ slug: "housing", label: "housing", source: "human" }],
            },
          ]),
        )
        .mockResolvedValueOnce(
          jsonOk({
            tags: [{ slug: "legal", label: "legal", source: "human" }],
          }),
        ),
    );
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("loads chunks and document tags", async () => {
    renderAdmin();

    expect(screen.getByText(/loading chunks/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("chunk-list")).toBeInTheDocument();
    });
    expect(screen.getByText("Chunk body text")).toBeInTheDocument();
    expect(screen.getByLabelText(/document tags/i)).toHaveValue("legal");
  });

  it("shows chunk load error", async () => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new Error("network down")),
    );

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("network down");
    });
  });

  it("saves document tags", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(
        jsonOk({
          tags: [{ slug: "housing", label: "housing", source: "human" }],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByLabelText(/document tags/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/document tags/i), {
      target: { value: "housing, legal-aid" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /save document tags/i }),
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        /document tags saved/i,
      );
    });
  });

  it("saves chunk tags and reloads chunks", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [{ slug: "new", label: "new", source: "human" }],
          },
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByLabelText(/chunk tags/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/chunk tags/i), {
      target: { value: "new-tag" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save chunk tags/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/chunk tags saved/i);
    });
  });

  it("queues retag job and polls until completed", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ job_id: "retag-job-1" }))
      .mockResolvedValueOnce(
        jsonOk({
          job_id: "retag-job-1",
          status: "running",
          urls: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      )
      .mockResolvedValueOnce(
        jsonOk({
          job_id: "retag-job-1",
          status: "completed",
          urls: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:01:00Z",
        }),
      )
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }));
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/retag job queued/i);
    });

    await vi.advanceTimersByTimeAsync(1600);
    await vi.advanceTimersByTimeAsync(1600);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/completed/i);
    });
  });

  it("shows retag job failure from polling", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ job_id: "retag-job-2" }))
      .mockResolvedValueOnce(
        jsonOk({
          job_id: "retag-job-2",
          status: "failed",
          urls: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:01:00Z",
          error_message: "LLM unavailable",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));
    await vi.advanceTimersByTimeAsync(1600);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("LLM unavailable");
    });
  });

  it("calls onClose when Close is clicked", async () => {
    const { onClose } = renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /close/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("uses document url when title is missing", async () => {
    const onClose = vi.fn();
    renderWithProviders(
      <ThemeProvider>
        <DocumentAdmin document={{ ...DOC, title: null }} onClose={onClose} />
      </ThemeProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(DOC.url)).toBeInTheDocument();
    });
  });

  it("silently ignores document tag load failures", async () => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          jsonOk([
            {
              chunk_id: "chunk-1",
              chunk_index: 0,
              text: "text",
              tags: [],
            },
          ]),
        )
        .mockRejectedValueOnce(new Error("tags unavailable")),
    );

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByTestId("chunk-list")).toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows generic errors for non-Error failures", async () => {
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockRejectedValueOnce("chunk load failed")
        .mockRejectedValueOnce(new Error("ignored")),
    );

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to load chunks",
      );
    });
  });

  it("shows save document tags error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce(new Error("patch failed"));
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByLabelText(/document tags/i)).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByRole("button", { name: /save document tags/i }),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("patch failed");
    });
  });

  it("shows save chunk tags error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce(new Error("chunk patch failed"));
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /save chunk tags/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /save chunk tags/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("chunk patch failed");
    });
  });

  it("shows retag queue error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce(new Error("retag queue failed"));
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("retag queue failed");
    });
  });

  it("shows poll error when job status check fails", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ job_id: "retag-job-3" }))
      .mockRejectedValueOnce("poll failed");
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));
    await vi.advanceTimersByTimeAsync(1600);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to poll retag job",
      );
    });
  });

  it("uses default message when retag job fails without details", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockResolvedValueOnce(jsonOk({ job_id: "retag-job-4" }))
      .mockResolvedValueOnce(
        jsonOk({
          job_id: "retag-job-4",
          status: "failed",
          urls: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:01:00Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));
    await vi.advanceTimersByTimeAsync(1600);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Retag job failed");
    });
  });

  it("shows generic save document tags error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce("patch boom");
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(screen.getByLabelText(/document tags/i)).toBeInTheDocument();
    });

    fireEvent.click(
      screen.getByRole("button", { name: /save document tags/i }),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to save document tags",
      );
    });
  });

  it("shows generic save chunk tags error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce("chunk boom");
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /save chunk tags/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /save chunk tags/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to save chunk tags",
      );
    });
  });

  it("shows generic retag queue error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonOk([
          {
            chunk_id: "chunk-1",
            chunk_index: 0,
            text: "text",
            tags: [],
          },
        ]),
      )
      .mockResolvedValueOnce(jsonOk({ tags: [] }))
      .mockRejectedValueOnce("retag boom");
    vi.stubGlobal("fetch", fetchMock);

    renderAdmin();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /llm re-tag/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /llm re-tag/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to queue retag job",
      );
    });
  });
});
