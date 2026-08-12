/**
 * UJ-080 / F75 — DM Automations panel: enable/disable + run history.
 * [Corpus: feature-list.md §F75]
 * [Corpus: user-journeys.md §UJ-080]
 * [Spec: docs/test-plan.md §TC-252, TC-255]
 * [Spec: docs/acceptance-criteria.md §AC-AU1, AC-AU5]
 */
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/components/ThemeProvider";
import { AutomationsPage } from "@/pages/AutomationsPage";

import { fetchInputUrl } from "./fetch-mock";
import { renderWithProviders } from "./renderWithProviders";

const CONFIG_ENABLED = {
  enabled: true,
  kill_switch: false,
  max_concurrent: 2,
};

const CONFIG_DISABLED = {
  enabled: false,
  kill_switch: false,
  max_concurrent: 2,
};

const CONFIG_KILL_SWITCH = {
  enabled: true,
  kill_switch: true,
  max_concurrent: 1,
};

const RUNS_BODY = {
  items: [
    {
      id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      job_type: "automation_catchup",
      status: "completed",
      started_at: "2026-08-07T10:00:00.000Z",
      finished_at: "2026-08-07T10:01:00.000Z",
      error: null,
      document_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      revision: "rev-1",
      created_at: "2026-08-07T10:00:00.000Z",
      updated_at: "2026-08-07T10:01:00.000Z",
    },
    {
      id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      job_type: "automation_catchup",
      status: "failed",
      started_at: "2026-08-07T09:00:00.000Z",
      finished_at: "2026-08-07T09:00:30.000Z",
      error: "embed timeout",
      document_id: null,
      revision: null,
      created_at: "2026-08-07T09:00:00.000Z",
      updated_at: "2026-08-07T09:00:30.000Z",
    },
  ],
  page: 1,
  page_size: 20,
  total_count: 2,
};

function renderAutomations() {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter initialEntries={["/automations"]}>
        <Routes>
          <Route path="/automations" element={<AutomationsPage />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("UJ-080 Automations panel (F75 / TC-252 / TC-255)", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("shows loading while config and runs load", () => {
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    renderAutomations();
    expect(screen.getByTestId("automations-admin-page")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders enable toggle, kill-switch state, and run history (AC-AU1 / AC-AU5)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_ENABLED,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => RUNS_BODY,
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByTestId("automations-enabled-toggle")).toBeChecked();
    });

    expect(screen.getByTestId("automations-kill-switch")).toHaveTextContent(
      /off/i,
    );
    expect(screen.getByTestId("automations-max-concurrent")).toHaveTextContent(
      "2",
    );

    const rows = await screen.findAllByTestId("automation-run-row");
    expect(rows).toHaveLength(2);
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText("embed timeout")).toBeInTheDocument();
    expect(screen.getAllByText("automation_catchup")).toHaveLength(2);
  });

  it("disables automations via PATCH and shows disabled state (TC-252)", async () => {
    let config = { ...CONFIG_ENABLED };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          if (url.includes("/automations/config") && init?.method === "PATCH") {
            config = { ...CONFIG_DISABLED };
            return Promise.resolve({
              ok: true,
              json: async () => config,
            });
          }
          if (url.includes("/automations/config")) {
            return Promise.resolve({
              ok: true,
              json: async () => config,
            });
          }
          if (url.includes("/automations/runs")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                items: [],
                page: 1,
                page_size: 20,
                total_count: 0,
              }),
            });
          }
          return Promise.resolve({ ok: true, json: async () => ({}) });
        }),
    );

    renderAutomations();

    const toggle = await screen.findByTestId("automations-enabled-toggle");
    expect(toggle).toBeChecked();

    fireEvent.click(toggle);

    await waitFor(() => {
      expect(
        screen.getByTestId("automations-enabled-toggle"),
      ).not.toBeChecked();
    });
    expect(screen.getByTestId("automations-enabled-status")).toHaveTextContent(
      /disabled/i,
    );

    const fetchMock = fetch as ReturnType<typeof vi.fn>;
    const patchCall = fetchMock.mock.calls.find((call) => {
      const init = call[1] as RequestInit | undefined;
      return init?.method === "PATCH";
    });
    expect(patchCall).toBeDefined();
    const patchInit = patchCall?.[1] as RequestInit;
    expect(JSON.parse(patchInit.body as string)).toEqual({
      enabled: false,
    });
  });

  it("shows kill-switch on when env kill-switch is active (TC-253 UI)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_KILL_SWITCH,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByTestId("automations-kill-switch")).toHaveTextContent(
        /on/i,
      );
    });
  });

  it("shows empty run history when there are no runs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_ENABLED,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByTestId("automations-runs-empty")).toBeInTheDocument();
    });
  });

  it("shows load error when config request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({}),
      }),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("shows loadFailed when load rejects a non-Error value", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue("backend down"),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to load/i);
    });
  });

  it("shows toggleFailed when PATCH rejects a non-Error value", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config") && init?.method === "PATCH") {
          return Promise.reject("patch refused");
        }
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_ENABLED,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();
    const toggle = await screen.findByTestId("automations-enabled-toggle");
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/failed to update/i);
    });
  });

  it("shows Error message when PATCH rejects an Error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config") && init?.method === "PATCH") {
          return Promise.reject(new Error("patch blew up"));
        }
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_ENABLED,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();
    fireEvent.click(await screen.findByTestId("automations-enabled-toggle"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("patch blew up");
    });
  });

  it("refresh button reloads config and runs", async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = fetchInputUrl(input);
      if (url.includes("/automations/config")) {
        return Promise.resolve({
          ok: true,
          json: async () => CONFIG_ENABLED,
        });
      }
      if (url.includes("/automations/runs")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            items: [],
            page: 1,
            page_size: 20,
            total_count: 0,
          }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderAutomations();
    await screen.findByTestId("automations-enabled-toggle");
    const before = fetchMock.mock.calls.length;

    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));

    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThan(before);
    });
  });

  it("ignores late load results after unmount", async () => {
    let resolveConfig: ((value: Response) => void) | undefined;
    const configPromise = new Promise<Response>((resolve) => {
      resolveConfig = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config")) {
          return configPromise;
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [],
              page: 1,
              page_size: 20,
              total_count: 0,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    const { unmount } = renderAutomations();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    unmount();
    resolveConfig?.(
      {
        ok: true,
        json: async () => CONFIG_ENABLED,
      } as Response,
    );
    await Promise.resolve();
  });

  it("renders pending run with emDash timestamps and secondary badge", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/automations/config")) {
          return Promise.resolve({
            ok: true,
            json: async () => CONFIG_ENABLED,
          });
        }
        if (url.includes("/automations/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                  job_type: "freshness_refresh",
                  status: "pending",
                  started_at: null,
                  finished_at: null,
                  error: null,
                  document_id: null,
                  revision: null,
                  created_at: "2026-08-07T11:00:00.000Z",
                  updated_at: "2026-08-07T11:00:00.000Z",
                },
              ],
              page: 1,
              page_size: 20,
              total_count: 1,
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );

    renderAutomations();

    await waitFor(() => {
      expect(screen.getByText("pending")).toBeInTheDocument();
    });
    expect(screen.getByText("freshness_refresh")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);
  });
});
