import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

const RUN_ID = "00000000-0000-0000-0000-000000000099";

const LIST_BODY = {
  items: [
    {
      run_id: RUN_ID,
      status: "completed",
      started_at: "2026-07-01T12:00:00Z",
      completed_at: "2026-07-01T12:01:00Z",
      metrics_summary: {
        retrieval_relevance: 0.91,
        faithfulness: 0.72,
        answer_relevancy: 0.68,
        latency_p95_ms: 4200,
      },
    },
  ],
  page: 1,
  page_size: 20,
  total_count: 1,
};

const DETAIL_BODY = {
  run_id: RUN_ID,
  status: "completed",
  metrics_summary: LIST_BODY.items[0].metrics_summary,
  items: [
    {
      case_id: "community-food-pantry",
      locale: "en",
      question: "When are food pantry hours updated?",
      expected_doc_url: "fixture://corpus/en/community-resources.md",
      retrieved_urls: ["fixture://corpus/en/community-resources.md"],
      answer: "Food pantry hours are posted weekly.",
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.85,
        answer_relevancy: 0.8,
        latency_ms: 3100,
      },
    },
    {
      case_id: "edge-abstain-mayor-phone",
      locale: "en",
      question: "What is the mayor's personal phone number?",
      retrieved_urls: [],
      answer: "I don't have enough community corpus context to answer that question.",
      metrics: {
        retrieval_pass: true,
        faithfulness: null,
        answer_relevancy: null,
        latency_ms: 1200,
      },
    },
  ],
};

describe("EvaluationPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/runs/")) {
          return Promise.resolve({
            ok: true,
            json: async () => DETAIL_BODY,
          });
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => LIST_BODY,
          });
        }
        if (url.includes("/internal/v1/stats")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              total_documents: 0,
              total_chunks: 0,
              tag_distribution: [],
              language_breakdown: {},
              recent_activity: [],
              top_served: [],
            }),
          });
        }
        if (url.includes("/internal/v1/documents")) {
          return Promise.resolve({ ok: true, json: async () => [] });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads history and per-question drill-down (TC-116)", async () => {
    await renderAppRoutesReady("/evaluation");

    expect(screen.getByTestId("evaluation-page")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });
    expect(screen.getByText(/91%/)).toBeInTheDocument();
    expect(screen.getByTestId("evaluation-drilldown")).toBeInTheDocument();
    expect(
      screen.getByText(/When are food pantry hours updated\?/),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Pass/i).length).toBeGreaterThan(0);
  });

  it("triggers a new eval run and refreshes detail", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-run-button")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("evaluation-run-button"));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
    const calls = vi.mocked(globalThis.fetch).mock.calls;
    const postCall = calls.find(
      (call) =>
        fetchInputUrl(call[0]).includes("/internal/v1/eval/runs") &&
        (call[1] as RequestInit | undefined)?.method === "POST",
    );
    expect(postCall).toBeDefined();
  });
});
