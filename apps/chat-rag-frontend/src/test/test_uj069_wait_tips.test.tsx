import { act, cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FACT_ROTATION_MS } from "../coldstart/constants";
import { COLD_START_FACTS } from "../coldstart/facts";
import { DEFAULT_WRWC_DONATE_URL } from "../coldstart/constants";
import { ColdStartWait } from "../components/ColdStartWait";
import { renderWithLocale } from "./renderWithLocale";

/**
 * UJ-069 / TC-216–217 — Vitest green companion to Playwright uj069-wait-tips.
 */
describe("UJ-069 / F64 wait tips + marketing", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem("vecinita.chat.coldstart.facts.v1");
  });

  it("TC-216: catalog kinds rotate in the wait shell; no survey", () => {
    vi.useFakeTimers();
    renderWithLocale(<ColdStartWait locale="en" active />);

    const kinds = new Set<string>();
    for (let i = 0; i < COLD_START_FACTS.length + 2; i += 1) {
      kinds.add(
        screen.getByTestId("cold-start-fact").getAttribute("data-kind") ?? "",
      );
      act(() => {
        vi.advanceTimersByTime(FACT_ROTATION_MS);
      });
    }

    expect(kinds.has("tip")).toBe(true);
    expect(kinds.has("marketing")).toBe(true);
    expect(kinds.has("fact")).toBe(true);
    expect(screen.queryByTestId("cold-start-survey")).not.toBeInTheDocument();
  });

  it("TC-217: consent accept + donate CTA unchanged with typed catalog", () => {
    renderWithLocale(<ColdStartWait locale="es" active />);

    expect(screen.getByTestId("cold-start-donate")).toHaveAttribute(
      "href",
      DEFAULT_WRWC_DONATE_URL,
    );
    fireEvent.click(screen.getByTestId("cold-start-consent-accept"));
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=1");
    expect(screen.queryByTestId("cold-start-consent")).not.toBeInTheDocument();
    const kind =
      screen.getByTestId("cold-start-fact").getAttribute("data-kind") ?? "";
    expect(["fact", "tip", "marketing"]).toContain(kind);
  });
});
