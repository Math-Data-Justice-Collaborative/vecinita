import {
  act,
  cleanup,
  fireEvent,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FACT_ROTATION_MS } from "../coldstart/constants";
import { COLD_START_FACTS } from "../coldstart/facts";
import { DEFAULT_WRWC_DONATE_URL } from "../coldstart/constants";
import { ColdStartWait } from "./ColdStartWait";
import { renderWithLocale } from "../test/renderWithLocale";

describe("ColdStartWait (TC-156, TC-158, TC-159, TC-216–217)", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem("vecinita.chat.coldstart.facts.v1");
  });

  it("shows starting-up status, a fact, and donate CTA when active", () => {
    const firstFact = COLD_START_FACTS[0];
    expect(firstFact).toBeDefined();
    renderWithLocale(<ColdStartWait locale="en" active />);

    expect(screen.getByRole("status")).toHaveTextContent(/starting up/i);
    expect(screen.getByTestId("cold-start-fact")).toHaveTextContent(
      firstFact?.en ?? "",
    );
    const donate = screen.getByTestId("cold-start-donate");
    expect(donate).toHaveAttribute("href", DEFAULT_WRWC_DONATE_URL);
    expect(donate).toHaveAttribute("target", "_blank");
    expect(donate.getAttribute("rel") ?? "").toMatch(/noopener/);
  });

  it("rotates facts on the rotation interval (TC-156)", () => {
    vi.useFakeTimers();
    const firstFact = COLD_START_FACTS[0];
    const secondFact = COLD_START_FACTS[1];
    expect(firstFact).toBeDefined();
    expect(secondFact).toBeDefined();
    renderWithLocale(<ColdStartWait locale="en" active />);

    expect(screen.getByTestId("cold-start-fact")).toHaveTextContent(
      firstFact?.en ?? "",
    );

    act(() => {
      vi.advanceTimersByTime(FACT_ROTATION_MS);
    });

    expect(screen.getByTestId("cold-start-fact")).toHaveTextContent(
      secondFact?.en ?? "",
    );
  });

  it("renders Spanish fact copy", () => {
    const firstFact = COLD_START_FACTS[0];
    expect(firstFact).toBeDefined();
    renderWithLocale(<ColdStartWait locale="es" active />);
    expect(screen.getByTestId("cold-start-fact")).toHaveTextContent(
      firstFact?.es ?? "",
    );
  });

  it("Accept remembers seen ids; No thanks opts out without memory (TC-158)", () => {
    const firstFact = COLD_START_FACTS[0];
    expect(firstFact).toBeDefined();
    renderWithLocale(<ColdStartWait locale="en" active />);

    const banner = screen.getByTestId("cold-start-consent");
    expect(within(banner).getByText(/not tracking/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("cold-start-consent-accept"));
    expect(screen.queryByTestId("cold-start-consent")).not.toBeInTheDocument();
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=1");
    expect(
      JSON.parse(
        localStorage.getItem("vecinita.chat.coldstart.facts.v1") ?? "[]",
      ),
    ).toContain(firstFact?.id);

    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem("vecinita.chat.coldstart.facts.v1");
    cleanup();

    renderWithLocale(<ColdStartWait locale="en" active />);
    fireEvent.click(screen.getByTestId("cold-start-consent-opt-out"));
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=0");
    expect(localStorage.getItem("vecinita.chat.coldstart.facts.v1")).toBeNull();
    expect(screen.getByTestId("cold-start-fact")).toBeInTheDocument();
  });

  it("hides when inactive", () => {
    renderWithLocale(<ColdStartWait locale="en" active={false} />);
    expect(screen.queryByTestId("cold-start-wait")).not.toBeInTheDocument();
  });

  it("exposes entry kind on the rotating message (TC-216)", () => {
    const first = COLD_START_FACTS[0];
    expect(first).toBeDefined();
    renderWithLocale(<ColdStartWait locale="en" active />);
    const node = screen.getByTestId("cold-start-fact");
    expect(node).toHaveAttribute("data-kind", first?.kind ?? "");
  });

  it("rotates tip and marketing kinds into the wait shell (TC-216)", () => {
    vi.useFakeTimers();
    renderWithLocale(<ColdStartWait locale="en" active />);
    const kinds = new Set<string>();
    kinds.add(
      screen.getByTestId("cold-start-fact").getAttribute("data-kind") ?? "",
    );
    for (let i = 0; i < COLD_START_FACTS.length + 2; i += 1) {
      act(() => {
        vi.advanceTimersByTime(FACT_ROTATION_MS);
      });
      kinds.add(
        screen.getByTestId("cold-start-fact").getAttribute("data-kind") ?? "",
      );
    }
    expect(kinds.has("tip")).toBe(true);
    expect(kinds.has("marketing")).toBe(true);
    expect(kinds.has("fact")).toBe(true);
  });

  it("does not render survey UI while wait is active (TC-216 / AC-UX1)", () => {
    renderWithLocale(<ColdStartWait locale="en" active />);
    expect(screen.queryByTestId("cold-start-survey")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("form", { name: /survey/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/mini survey/i)).not.toBeInTheDocument();
  });

  it("keeps donate + consent with typed catalog (TC-217 / AC-UX2)", () => {
    renderWithLocale(<ColdStartWait locale="en" active />);
    expect(screen.getByTestId("cold-start-donate")).toHaveAttribute(
      "href",
      DEFAULT_WRWC_DONATE_URL,
    );
    expect(screen.getByTestId("cold-start-consent")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("cold-start-consent-accept"));
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=1");
    expect(screen.queryByTestId("cold-start-consent")).not.toBeInTheDocument();
    expect(screen.getByTestId("cold-start-fact")).toBeInTheDocument();
  });
});
