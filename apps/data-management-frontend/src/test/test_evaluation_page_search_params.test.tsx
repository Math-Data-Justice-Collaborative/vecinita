import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import React from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { EvaluationPage } from "@/pages/EvaluationPage";

import { fetchInputUrl } from "./fetch-mock";
import { mockOllamaApiFetch } from "./helpers/mockOllamaApi";

const setSearchParams = vi.fn<
  (updater: (prev: URLSearchParams) => URLSearchParams) => void
>();

vi.mock("@/config", () => ({
  requireCorpusConfig: () => ({
    baseUrl: "http://localhost:8002",
    apiKey: "test-corpus-key",
  }),
}));

vi.mock("@/components/ui/tabs", () => {
  const TabsContext = React.createContext<{
    onValueChange?: (value: string) => void;
  }>({});

  const Tabs = ({
    onValueChange,
    children,
    ...props
  }: {
    onValueChange?: (value: string) => void;
    children: React.ReactNode;
    "data-testid"?: string;
  }) => (
    <TabsContext.Provider value={{ onValueChange }}>
      <div {...props}>{children}</div>
    </TabsContext.Provider>
  );

  const TabsList = ({ children }: { children: React.ReactNode }) => (
    <div role="tablist">{children}</div>
  );

  const TabsTrigger = ({
    value,
    children,
    ...props
  }: {
    value: string;
    children: React.ReactNode;
    "data-testid"?: string;
  }) => {
    const ctx = React.useContext(TabsContext);
    return (
      <button
        type="button"
        role="tab"
        {...props}
        onClick={() => {
          ctx.onValueChange?.(value);
        }}
      >
        {children}
      </button>
    );
  };

  const TabsContent = ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  );

  return { Tabs, TabsList, TabsTrigger, TabsContent };
});

vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );
  return {
    ...actual,
    useSearchParams: () => [
      new URLSearchParams({ tab: "runs" }),
      setSearchParams,
    ],
  };
});

function renderPage(ui: ReactElement) {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <LocaleProvider>
      <MemoryRouter>{children}</MemoryRouter>
    </LocaleProvider>
  );
  return render(ui, { wrapper });
}

const LIST_BODY = {
  items: [],
  page: 1,
  page_size: 20,
  total_count: 0,
};

describe("EvaluationPage search params", () => {
  beforeEach(() => {
    setSearchParams.mockReset();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/criteria")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [] }),
          });
        }
        if (url.includes("/internal/v1/eval/runs/timeseries")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ points: [], available_metrics: [] }),
          });
        }
        const ollamaMock = mockOllamaApiFetch(url);
        if (ollamaMock !== null) {
          return Promise.resolve(ollamaMock);
        }
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [] }),
          });
        }
        if (url.includes("/internal/v1/eval/runs")) {
          return Promise.resolve({
            ok: true,
            json: async () => LIST_BODY,
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls setSearchParams when switching evaluation tabs", async () => {
    renderPage(<EvaluationPage />);
    await waitFor(() => {
      expect(screen.getByTestId("eval-tab-explore")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-tab-explore"));
    expect(setSearchParams).toHaveBeenCalledTimes(1);
    const updater = setSearchParams.mock.calls[0]?.[0];
    expect(updater).toBeDefined();
    const next = updater(new URLSearchParams({ tab: "runs" }));
    expect(next.get("tab")).toBe("explore");
  });
});
