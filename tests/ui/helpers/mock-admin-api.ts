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

function evalRunsList() {
  return {
    items: [
      {
        run_id: "00000000-0000-0000-0000-000000000099",
        status: "completed",
        metrics_summary: TIMESERIES_BODY.points[0].metrics_summary,
      },
    ],
    page: 1,
    page_size: 20,
    total_count: 1,
  };
}

function evalRunDetail() {
  return {
    run_id: "00000000-0000-0000-0000-000000000099",
    status: "completed",
    metrics_summary: TIMESERIES_BODY.points[0].metrics_summary,
    items: [
      {
        case_id: "community-food-pantry",
        locale: "en",
        question: "When are food pantry hours updated?",
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
        type: "ingest",
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
            type: "ingest",
            created_at: "2026-07-01T12:00:00Z",
            updated_at: "2026-07-01T12:01:00Z",
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
  if (url.includes("/internal/v1/eval/runs/") && method === "GET") {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...evalRunDetail(),
        run_id: url.split("/").pop() ?? evalRunDetail().run_id,
        status: "completed",
      }),
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
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        run_id: "00000000-0000-0000-0000-0000000000aa",
        status: "pending",
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
  await page.route("**/jobs**", fulfillJobsRoute);
  await page.route("**/internal/v1/**", fulfillAdminRoute);
}

export async function mockAuthenticatedAdmin(page: Page): Promise<void> {
  const { seedAdminSession } = await import("./mock-admin-auth");
  await seedAdminSession(page);
  await mockAdminApi(page);
}

export async function mockAuthenticatedViewer(page: Page): Promise<void> {
  const { seedViewerSession } = await import("./mock-admin-auth");
  await seedViewerSession(page);
  await mockAdminApi(page);
}
