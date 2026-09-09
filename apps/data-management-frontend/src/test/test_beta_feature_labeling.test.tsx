/**
 * UJ-099 / F86 — Beta feature labeling + feedback link (TC-338, TC-339).
 *
 * [Corpus: feature-list.md §F86]
 * [Corpus: user-journeys.md §UJ-099]
 * [Spec: docs/test-plan.md §TC-338 §TC-339]
 * [Spec: docs/acceptance-criteria.md §AC-BETA1 §AC-BETA2 §AC-BETA3]
 */
import { cleanup, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BetaFeatureNotice } from "@/components/BetaFeatureNotice";
import { FinetunePage } from "@/pages/FinetunePage";
import { BETA_FEEDBACK_ISSUE_URL } from "@/config/beta";

import { fetchInputUrl } from "./fetch-mock";
import { renderAppRoutesReady } from "./renderAppHelpers";
import { renderWithProviders } from "./renderWithProviders";

const PIN_BASE = { adapter_id: null, base: true };

function jsonOk(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe("BetaFeatureNotice (TC-338)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders badge, banner, and feedback link with noopener", () => {
    renderWithProviders(<BetaFeatureNotice feature="finetune" />);

    const badge = screen.getByTestId("beta-feature-badge");
    expect(badge).toHaveTextContent(/beta/i);

    const banner = screen.getByTestId("beta-feature-banner-finetune");
    expect(banner).toBeInTheDocument();

    const link = screen.getByTestId("beta-feature-feedback-link-finetune");
    expect(link).toHaveAttribute("href", BETA_FEEDBACK_ISSUE_URL);
    expect(link).toHaveAttribute("target", "_blank");
    expect(link.getAttribute("rel") ?? "").toMatch(/noopener/);
    expect(link.getAttribute("rel") ?? "").toMatch(/noreferrer/);
  });

  it("renders compact chip for nav", () => {
    renderWithProviders(<BetaFeatureNotice feature="playground" compact />);
    expect(screen.getByTestId("beta-feature-nav-chip")).toHaveTextContent(
      /beta/i,
    );
    expect(screen.queryByTestId("beta-feature-banner")).not.toBeInTheDocument();
  });

  it("renders playground banner for model-download reuse (AC-BETA1)", () => {
    renderWithProviders(<BetaFeatureNotice feature="playground" />);
    expect(
      screen.getByTestId("beta-feature-banner-playground"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("beta-feature-feedback-link-playground"),
    ).toHaveAttribute("href", BETA_FEEDBACK_ISSUE_URL);
  });
});

describe("Fine-tune Beta chrome (TC-338)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/finetune/adapter")) {
          return Promise.resolve(jsonOk(PIN_BASE));
        }
        if (url.includes("/jobs")) {
          return Promise.resolve(jsonOk({ jobs: [] }));
        }
        return Promise.resolve(jsonOk({}));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows Beta banner on Fine-tune page", async () => {
    renderWithProviders(
      <MemoryRouter initialEntries={["/finetune"]}>
        <Routes>
          <Route path="/finetune" element={<FinetunePage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("finetune-admin-page")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId("beta-feature-banner-finetune"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("beta-feature-feedback-link-finetune"),
    ).toHaveAttribute("href", BETA_FEEDBACK_ISSUE_URL);
  });
});

describe("Admin nav Beta chips (TC-339)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/stats")) {
          return Promise.resolve(
            jsonOk({
              total_documents: 0,
              total_chunks: 0,
              tag_distribution: [],
              language_breakdown: {},
              recent_activity: [],
              top_served: [],
            }),
          );
        }
        return Promise.resolve(jsonOk({}));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows Beta chips on Fine-tune and Evaluation nav only", async () => {
    await renderAppRoutesReady("/dashboard");

    expect(screen.getByTestId("beta-nav-chip-finetune")).toBeInTheDocument();
    expect(screen.getByTestId("beta-nav-chip-evaluation")).toBeInTheDocument();
    expect(
      screen.queryByTestId("beta-nav-chip-dashboard"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("beta-nav-chip-corpus"),
    ).not.toBeInTheDocument();
  });
});
