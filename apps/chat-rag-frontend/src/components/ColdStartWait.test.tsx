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

describe("ColdStartWait (TC-156, TC-158, TC-159)", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    document.cookie =
      "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
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
    expect(
      within(banner).getByText(/not tracking/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("cold-start-consent-accept"));
    expect(screen.queryByTestId("cold-start-consent")).not.toBeInTheDocument();
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=1");
    expect(
      JSON.parse(
        localStorage.getItem("vecinita.chat.coldstart.facts.v1") ?? "[]",
      ),
    ).toContain(firstFact?.id);

    document.cookie =
      "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem("vecinita.chat.coldstart.facts.v1");
    cleanup();

    renderWithLocale(<ColdStartWait locale="en" active />);
    fireEvent.click(screen.getByTestId("cold-start-consent-opt-out"));
    expect(document.cookie).toContain("vecinita_chat_coldstart_consent=0");
    expect(
      localStorage.getItem("vecinita.chat.coldstart.facts.v1"),
    ).toBeNull();
    expect(screen.getByTestId("cold-start-fact")).toBeInTheDocument();
  });

  it("hides when inactive", () => {
    renderWithLocale(<ColdStartWait locale="en" active={false} />);
    expect(screen.queryByTestId("cold-start-wait")).not.toBeInTheDocument();
  });
});
