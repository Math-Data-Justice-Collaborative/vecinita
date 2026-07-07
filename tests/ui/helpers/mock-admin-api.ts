import type { Page, Route } from "@playwright/test";

const TIMESERIES_BODY = {
  points: [
    {
      run_id: "00000000-0000-0000-0000-000000000099",
      completed_at: "2026-07-01T12:01:00Z",
      metrics_summary: {
        retrieval_relevance: 0.91,
        faithfulness: 0.72,
        answer_relevancy: 0.68,
        latency_p95_ms: 4200,
      },
    },
  ],
  available_metrics: [
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
    "latency_p95_ms",
  ],
};

const CRITERIA_BODY = {
  items: [
    {
      criterion_id: "00000000-0000-0000-0000-000000000077",
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
      scorer_type: "llm_rubric",
      enabled: true,
      created_at: "2026-07-01T12:00:00Z",
      updated_at: "2026-07-01T12:00:00Z",
    },
  ],
};

const STATS_BODY = {
  total_documents: 0,
  total_chunks: 0,
  tag_distribution: [],
  language_breakdown: {},
  recent_activity: [],
  top_served: [],
};

const RUN_A_ID = "00000000-0000-0000-0000-000000000099";
const RUN_B_ID = "00000000-0000-0000-0000-000000000088";
const PLAYGROUND_RUN_ID = "00000000-0000-0000-0000-0000000000aa";
/** Eval run surfaced on unified GET /jobs (UJ-044 / TC-124). */
export const EVAL_JOB_ID = "55555555-5555-4555-8555-555555555555";

const OLLAMA_MODELS_BODY = {
  items: [
    { model_id: "qwen2.5:1.5b-instruct", available: true },
    { model_id: "llama3.2:3b", available: true },
  ],
};

const EVAL_CONFIG_PRESETS_BODY = { items: [] };

function evalRunsList() {
  return {
    items: [
      {
        run_id: RUN_A_ID,
        status: "completed",
        metrics_summary: {
          retrieval_relevance: 0.91,
          faithfulness: 0.85,
          answer_relevancy: 0.8,
          latency_p95_ms: 3200,
        },
      },
      {
        run_id: RUN_B_ID,
        status: "completed",
        metrics_summary: {
          retrieval_relevance: 0.88,
          faithfulness: 0.55,
          answer_relevancy: 0.72,
          latency_p95_ms: 4100,
        },
      },
    ],
    page: 1,
    page_size: 20,
    total_count: 2,
  };
}

function evalRunDetail(runId: string) {
  if (runId === RUN_B_ID) {
    return {
      run_id: RUN_B_ID,
      status: "completed",
      metrics_summary: {
        retrieval_relevance: 0.88,
        faithfulness: 0.55,
        answer_relevancy: 0.72,
        latency_p95_ms: 4100,
      },
      items: [
        {
          case_id: "community-food-pantry",
          locale: "en",
          question: "When are food pantry hours updated?",
          answer: "Hours update every Monday morning.",
          metrics: {
            retrieval_pass: true,
            faithfulness: 0.55,
            answer_relevancy: 0.72,
            latency_ms: 3900,
          },
        },
      ],
    };
  }
  return {
    run_id: runId,
    status: "completed",
    metrics_summary: {
      retrieval_relevance: 0.91,
      faithfulness: 0.85,
      answer_relevancy: 0.8,
      latency_p95_ms: 3200,
    },
    items: [
      {
        case_id: "community-food-pantry",
        locale: "en",
        question: "When are food pantry hours updated?",
        answer: "Food pantry hours are posted weekly.",
        metrics: {
          retrieval_pass: true,
          faithfulness: 0.85,
          answer_relevancy: 0.8,
          latency_ms: 3100,
        },
      },
    ],
  };
}

async function fulfillJobsRoute(route: Route): Promise<void> {
  const url = route.request().url();
  const method = route.request().method();

  if (method === "POST" && url.endsWith("/jobs")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ job_id: "job-playwright-001" }),
    });
    return;
  }
  if (method === "GET" && url.includes("/jobs/job-playwright-001")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "job-playwright-001",
        status: "completed",
        job_type: "ingest",
        urls: ["https://example.com/page-a"],
        error_code: null,
        error_message: null,
        created_at: "2026-07-01T12:00:00Z",
        updated_at: "2026-07-01T12:01:00Z",
      }),
    });
    return;
  }
  if (method === "GET" && url.endsWith("/jobs")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        jobs: [
          {
            job_id: "job-playwright-001",
            status: "completed",
            job_type: "ingest",
            urls: ["https://example.com/page-a"],
            error_code: null,
            error_message: null,
            created_at: "2026-07-01T12:00:00Z",
            updated_at: "2026-07-01T12:01:00Z",
          },
          {
            job_id: EVAL_JOB_ID,
            status: "running",
            job_type: "eval",
            urls: [],
            error_code: null,
            error_message: null,
            created_at: "2026-07-02T12:00:00Z",
            updated_at: "2026-07-02T12:00:05Z",
          },
        ],
      }),
    });
    return;
  }
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ jobs: [] }),
  });
}

async function fulfillAdminRoute(route: Route): Promise<void> {
  const url = route.request().url();
  const method = route.request().method();

  if (url.includes("/internal/v1/stats")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(STATS_BODY),
    });
    return;
  }
  if (url.includes("/internal/v1/documents")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
    return;
  }
  if (url.includes("/internal/v1/health")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/runs/timeseries")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(TIMESERIES_BODY),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/criteria") && method === "GET") {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(CRITERIA_BODY),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/criteria") && method === "POST") {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        criterion_id: "00000000-0000-0000-0000-000000000066",
        slug: "new-criterion",
        label: "New",
        rubric: "Rubric",
        scorer_type: "llm_rubric",
        enabled: true,
        created_at: "2026-07-01T12:00:00Z",
        updated_at: "2026-07-01T12:00:00Z",
      }),
    });
    return;
  }
  if (url.includes("/internal/v1/models/ollama/catalog/")) {
    const slug = decodeURIComponent(
      url.split("/internal/v1/models/ollama/catalog/")[1] ?? "",
    );
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        slug,
        tags: OLLAMA_MODELS_BODY.items,
      }),
    });
    return;
  }
  if (url.includes("/internal/v1/models/ollama/catalog")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        families: [{ slug: "qwen2.5" }],
      }),
    });
    return;
  }
  if (url.includes("/internal/v1/models/ollama")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(OLLAMA_MODELS_BODY),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/config-presets")) {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EVAL_CONFIG_PRESETS_BODY),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/runs/") && method === "GET") {
    const runId = url.split("/").pop() ?? RUN_A_ID;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(evalRunDetail(runId)),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/runs") && method === "GET") {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(evalRunsList()),
    });
    return;
  }
  if (url.includes("/internal/v1/eval/runs") && method === "POST") {
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        run_id: PLAYGROUND_RUN_ID,
        status: "pending",
        created_at: "2026-07-02T12:00:00Z",
      }),
    });
    return;
  }
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({}),
  });
}

/** Mock internal-write-api routes for authenticated admin navigation tests. */
export async function mockAdminApi(page: Page): Promise<void> {
  await page.route("http://127.0.0.1:8001/jobs**", fulfillJobsRoute);
  await page.route("**/internal/v1/**", fulfillAdminRoute);
}

export async function mockAuthenticatedAdmin(page: Page): Promise<void> {
  const { seedAdminSession } = await import("./mock-admin-auth");
  await seedAdminSession(page);
  await mockAdminApi(page);
}

export async function mockAuthenticatedSuperAdmin(page: Page): Promise<void> {
  const { seedSuperAdminSession } = await import("./mock-admin-auth");
  await seedSuperAdminSession(page);
  await mockAdminApi(page);
}

export async function mockAuthenticatedViewer(page: Page): Promise<void> {
  const { seedViewerSession } = await import("./mock-admin-auth");
  await seedViewerSession(page);
  await mockAdminApi(page);
}
