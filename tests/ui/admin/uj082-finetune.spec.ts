import { expect, test, type Page, type Route } from "@playwright/test";

import { mockAuthenticatedAdmin } from "../helpers/mock-admin-api";

/**
 * UJ-082 / F77: Fine-tune panel — approve, eval, human promote, rollback.
 * [Corpus: feature-list.md §F77]
 * [Corpus: user-journeys.md §UJ-082]
 * [Spec: docs/test-plan.md §TC-260 §TC-261 §TC-262 §TC-265]
 * [Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT3 §AC-FT4 §AC-FT9]
 */

export const FT_RUN_ID = "11111111-1111-4111-8111-111111111111";
export const FT_ADAPTER_ID = "adapter-playwright-uj082";

const EVAL_REPORT = {
  run_id: FT_RUN_ID,
  adapter_id: FT_ADAPTER_ID,
  base_model_id: "qwen2.5:1.5b-instruct",
  base: {
    faithfulness: 0.7,
    answer_relevancy: 0.6,
    questions_scored: 2,
  },
  adapter: {
    faithfulness: 0.72,
    answer_relevancy: 0.65,
    questions_scored: 2,
  },
  auto_promote: false,
  summary:
    "Human judgment required — no automated promote (RD-338 / AC-FT4). Promote only when the operator judges the adapter better than base.",
};

type FtJob = {
  job_id: string;
  status: string;
  job_type: string;
  urls: string[];
  approved: boolean;
  created_at: string;
  updated_at: string;
  metrics?: {
    finetune_outcome: string;
    adapter_id: string;
    adapter_path: string;
    pair_count: number;
    base_model_id: string;
  };
};

async function mockFinetuneApis(page: Page): Promise<void> {
  let pin: { adapter_id: string | null; base: boolean } = {
    adapter_id: null,
    base: true,
  };
  let jobs: FtJob[] = [
    {
      job_id: FT_RUN_ID,
      status: "pending",
      job_type: "finetune_train",
      urls: [],
      approved: false,
      created_at: "2026-08-12T10:00:00.000Z",
      updated_at: "2026-08-12T10:00:00.000Z",
    },
  ];

  await page.route("**/jobs**", async (route: Route) => {
    const request = route.request();
    const url = request.url();
    const method = request.method();
    const path = new URL(url).pathname;

    if (method === "GET" && path.endsWith("/jobs/events")) {
      await route.fulfill({
        status: 503,
        body: "sse unavailable in playwright mock",
      });
      return;
    }

    if (method === "POST" && path.endsWith("/jobs")) {
      const newId = "33333333-3333-4333-8333-333333333333";
      jobs = [
        {
          job_id: newId,
          status: "pending",
          job_type: "finetune_train",
          urls: [],
          approved: false,
          created_at: "2026-08-12T11:00:00.000Z",
          updated_at: "2026-08-12T11:00:00.000Z",
        },
        ...jobs,
      ];
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({ job_id: newId, status: "pending" }),
      });
      return;
    }

    const approveMatch = path.match(/\/jobs\/([^/]+)\/approve$/);
    if (method === "POST" && approveMatch?.[1]) {
      const jobId = decodeURIComponent(approveMatch[1]);
      jobs = jobs.map((job) =>
        job.job_id === jobId
          ? {
              ...job,
              approved: true,
              status: "completed",
              metrics: {
                finetune_outcome: "trained",
                adapter_id: FT_ADAPTER_ID,
                adapter_path: `/adapters/${FT_ADAPTER_ID}`,
                pair_count: 8,
                base_model_id: "qwen2.5:1.5b-instruct",
              },
            }
          : job,
      );
      const updated = jobs.find((j) => j.job_id === jobId);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(updated),
      });
      return;
    }

    if (method === "GET" && path.endsWith("/jobs")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ jobs }),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/internal/v1/finetune/**", async (route: Route) => {
    const request = route.request();
    const url = request.url();
    const method = request.method();

    if (url.includes("/finetune/adapter") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(pin),
      });
      return;
    }

    if (url.includes("/finetune/runs/") && url.includes("/eval") && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(EVAL_REPORT),
      });
      return;
    }

    if (url.includes("/finetune/promote") && method === "POST") {
      const raw = request.postData() ?? "{}";
      const body = JSON.parse(raw) as {
        adapter_id?: string;
        rollback?: boolean;
      };
      if (body.rollback) {
        pin = { adapter_id: null, base: true };
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            promoted: false,
            adapter_id: null,
            base: true,
            auto_promote: false,
          }),
        });
        return;
      }
      pin = { adapter_id: body.adapter_id ?? FT_ADAPTER_ID, base: false };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          promoted: true,
          adapter_id: pin.adapter_id,
          base: false,
          auto_promote: false,
        }),
      });
      return;
    }

    await route.fallback();
  });
}

test.describe("Fine-tune panel (UJ-082)", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedAdmin(page);
    await mockFinetuneApis(page);
  });

  test("nav opens Fine-tune; request train and approve (TC-260)", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    await page.getByRole("link", { name: /fine-tune/i }).click();
    await expect(page).toHaveURL(/\/finetune/);
    await expect(page.getByTestId("finetune-admin-page")).toBeVisible();
    await expect(page.getByTestId("finetune-prod-pin")).toContainText(/base/i);

    const createPromise = page.waitForRequest(
      (req) =>
        req.method() === "POST" &&
        req.url().includes("/jobs") &&
        !req.url().includes("/approve"),
    );
    await page.getByTestId("finetune-request-train-btn").click();
    const createReq = await createPromise;
    expect(JSON.parse(createReq.postData() ?? "{}")).toEqual({
      urls: [],
      options: { job_type: "finetune_train" },
    });

    await expect(page.getByTestId("finetune-job-row").first()).toBeVisible();
    await expect(page.getByTestId("finetune-approve-btn").first()).toBeVisible();

    const approvePromise = page.waitForRequest(
      (req) => req.method() === "POST" && req.url().includes("/approve"),
    );
    await page.getByTestId("finetune-approve-btn").first().click();
    await approvePromise;

    await expect(page.getByTestId("finetune-view-eval-btn").first()).toBeVisible();
  });

  test("view eval, human-confirm promote, then rollback (TC-261/262/265)", async ({
    page,
  }) => {
    // Seed a completed train so View eval is available without approve first.
    await page.route("**/jobs**", async (route: Route) => {
      const path = new URL(route.request().url()).pathname;
      if (route.request().method() === "GET" && path.endsWith("/jobs")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            jobs: [
              {
                job_id: FT_RUN_ID,
                status: "completed",
                job_type: "finetune_train",
                urls: [],
                approved: true,
                created_at: "2026-08-12T10:00:00.000Z",
                updated_at: "2026-08-12T10:05:00.000Z",
                metrics: {
                  finetune_outcome: "trained",
                  adapter_id: FT_ADAPTER_ID,
                  adapter_path: `/adapters/${FT_ADAPTER_ID}`,
                  pair_count: 8,
                  base_model_id: "qwen2.5:1.5b-instruct",
                },
              },
            ],
          }),
        });
        return;
      }
      await route.fallback();
    });

    await page.goto("/finetune");
    await expect(page.getByTestId("finetune-admin-page")).toBeVisible();
    await expect(page.getByTestId("finetune-prod-pin")).toContainText(/base/i);

    const evalPromise = page.waitForRequest(
      (req) =>
        req.method() === "GET" &&
        req.url().includes(`/finetune/runs/${FT_RUN_ID}/eval`),
    );
    await page.getByTestId("finetune-view-eval-btn").click();
    await evalPromise;

    await expect(page.getByTestId("finetune-eval-report")).toBeVisible();
    await expect(page.getByTestId("finetune-eval-base-faithfulness")).toHaveText(
      "0.7",
    );
    await expect(
      page.getByTestId("finetune-eval-adapter-faithfulness"),
    ).toHaveText("0.72");
    await expect(page.getByTestId("finetune-auto-promote")).toContainText(
      /false/i,
    );

    const promoteBtn = page.getByTestId("finetune-promote-btn");
    await expect(promoteBtn).toBeDisabled();

    await page.getByTestId("finetune-promote-confirm").check();
    await expect(promoteBtn).toBeEnabled();

    const promotePromise = page.waitForRequest(
      (req) =>
        req.method() === "POST" && req.url().includes("/finetune/promote"),
    );
    await promoteBtn.click();
    const promoteReq = await promotePromise;
    expect(JSON.parse(promoteReq.postData() ?? "{}")).toEqual({
      adapter_id: FT_ADAPTER_ID,
    });
    await expect(page.getByTestId("finetune-prod-pin")).toContainText(
      FT_ADAPTER_ID,
    );

    const rollbackPromise = page.waitForRequest((req) => {
      if (req.method() !== "POST" || !req.url().includes("/finetune/promote")) {
        return false;
      }
      const body = JSON.parse(req.postData() ?? "{}") as { rollback?: boolean };
      return body.rollback === true;
    });
    await page.getByTestId("finetune-rollback-btn").click();
    await rollbackPromise;
    await expect(page.getByTestId("finetune-prod-pin")).toContainText(/base/i);
  });
});
