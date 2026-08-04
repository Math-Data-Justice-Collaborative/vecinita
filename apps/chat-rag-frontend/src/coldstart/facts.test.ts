import { afterEach, describe, expect, it } from "vitest";

import { COLD_START_FACTS_STORAGE_KEY } from "./constants";
import { COLD_START_FACTS, factText, pickNextFact } from "./facts";
import { setColdStartConsent, rememberSeenFactId } from "./prefs";
import { resolveDonateUrl } from "./donateUrl";
import { DEFAULT_WRWC_DONATE_URL } from "./constants";

describe("coldstart facts", () => {
  afterEach(() => {
    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem(COLD_START_FACTS_STORAGE_KEY);
  });

  it("curates about ten bilingual facts from the Phase 0 pool", () => {
    expect(COLD_START_FACTS.length).toBeGreaterThanOrEqual(8);
    expect(COLD_START_FACTS.length).toBeLessThanOrEqual(12);
    for (const fact of COLD_START_FACTS) {
      expect(fact.en.length).toBeGreaterThan(10);
      expect(fact.es.length).toBeGreaterThan(10);
      expect(factText(fact, "en")).toBe(fact.en);
      expect(factText(fact, "es")).toBe(fact.es);
    }
  });

  it("cycles facts by index when memory is off", () => {
    const first = pickNextFact(0);
    const expectedFirst = COLD_START_FACTS[0];
    expect(expectedFirst).toBeDefined();
    expect(first.fact.id).toBe(expectedFirst?.id);
    const second = pickNextFact(first.nextIndex);
    const expectedSecond = COLD_START_FACTS[1];
    expect(expectedSecond).toBeDefined();
    expect(second.fact.id).toBe(expectedSecond?.id);
  });

  it("prefers unseen facts after Accept memory", () => {
    const firstFact = COLD_START_FACTS[0];
    expect(firstFact).toBeDefined();
    if (!firstFact) {
      return;
    }
    setColdStartConsent("accept");
    rememberSeenFactId(firstFact.id);
    const picked = pickNextFact(0, { preferUnseen: true });
    expect(picked.fact.id).not.toBe(firstFact.id);
  });
});

describe("resolveDonateUrl (TC-159)", () => {
  it("defaults to wrwc.org/donate/", () => {
    expect(resolveDonateUrl(undefined)).toBe(DEFAULT_WRWC_DONATE_URL);
    expect(resolveDonateUrl("")).toBe(DEFAULT_WRWC_DONATE_URL);
  });

  it("uses VITE override with trailing slash", () => {
    expect(resolveDonateUrl("https://example.org/give")).toBe(
      "https://example.org/give/",
    );
  });
});
