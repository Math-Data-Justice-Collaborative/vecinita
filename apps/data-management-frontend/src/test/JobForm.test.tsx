import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { JobForm } from "../components/JobForm";

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("JobForm", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("parses URLs and shows completed job status", async () => {
    const fetchMock = vi
      .fn<(input: RequestInfo | URL, init?: RequestInit) => Promise<Response>>()
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "11111111-1111-4111-8111-111111111111",
          status: "pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          job_id: "11111111-1111-4111-8111-111111111111",
          status: "completed",
          urls: ["https://example.com/page"],
          created_at: "2026-05-19T00:00:00Z",
          updated_at: "2026-05-19T00:00:01Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<JobForm />);
    fireEvent.change(screen.getByLabelText(/public urls/i), {
      target: { value: "https://example.com/page\n" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));

    await waitFor(() => {
      expect(screen.getByTestId("job-status")).toHaveTextContent("completed");
    });
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.method).toBe("POST");
    const headers = new Headers(init?.headers);
    expect(headers.get("X-Vecinita-Proxy-Key")).toBe("test-proxy-key");
  });

  it("shows validation error when no URLs entered", async () => {
    render(<JobForm />);
    fireEvent.click(screen.getByRole("button", { name: /submit ingest/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /at least one url/i,
    );
  });
});
