import { afterEach, describe, expect, it } from "vitest";

import { COLD_START_FACTS_STORAGE_KEY } from "./constants";
import {
  COLD_START_FACTS,
  entryText,
  factText,
  pickNextFact,
  type ColdStartEntryKind,
} from "./facts";
import { setColdStartConsent, rememberSeenFactId } from "./prefs";
import { resolveDonateUrl } from "./donateUrl";
import { DEFAULT_WRWC_DONATE_URL } from "./constants";

describe("coldstart facts", () => {
  afterEach(() => {
    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem(COLD_START_FACTS_STORAGE_KEY);
  });

  it("curates about ten bilingual facts from the Phase 0 pool", () => {
    const facts = COLD_START_FACTS.filter((e) => e.kind === "fact");
    expect(facts.length).toBeGreaterThanOrEqual(8);
    expect(facts.length).toBeLessThanOrEqual(12);
    for (const fact of facts) {
      expect(fact.en.length).toBeGreaterThan(10);
      expect(fact.es.length).toBeGreaterThan(10);
      expect(factText(fact, "en")).toBe(fact.en);
      expect(factText(fact, "es")).toBe(fact.es);
      expect(entryText(fact, "en")).toBe(fact.en);
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

describe("typed wait catalog (TC-216 / F64 / AC-UX1)", () => {
  afterEach(() => {
    document.cookie = "vecinita_chat_coldstart_consent=; Path=/; Max-Age=0";
    localStorage.removeItem(COLD_START_FACTS_STORAGE_KEY);
  });

  it("includes tip and marketing kinds alongside fact", () => {
    const kinds = new Set(COLD_START_FACTS.map((e) => e.kind));
    expect(kinds.has("fact")).toBe(true);
    expect(kinds.has("tip")).toBe(true);
    expect(kinds.has("marketing")).toBe(true);

    const tips = COLD_START_FACTS.filter((e) => e.kind === "tip");
    const marketing = COLD_START_FACTS.filter((e) => e.kind === "marketing");
    expect(tips.length).toBeGreaterThanOrEqual(2);
    expect(marketing.length).toBeGreaterThanOrEqual(2);

    for (const entry of [...tips, ...marketing]) {
      expect(entry.en.length).toBeGreaterThan(10);
      expect(entry.es.length).toBeGreaterThan(10);
      expect(entryText(entry, "en")).toBe(entry.en);
      expect(entryText(entry, "es")).toBe(entry.es);
    }
  });

  it("rotates through tip and marketing entries in the catalog cycle", () => {
    const seen = new Set<ColdStartEntryKind>();
    let index = 0;
    for (let i = 0; i < COLD_START_FACTS.length * 2; i += 1) {
      const picked = pickNextFact(index);
      seen.add(picked.fact.kind);
      index = picked.nextIndex;
    }
    expect(seen.has("tip")).toBe(true);
    expect(seen.has("marketing")).toBe(true);
    expect(seen.has("fact")).toBe(true);
  });

  it("does not include survey-like entries in the catalog", () => {
    for (const entry of COLD_START_FACTS) {
      const blob = `${entry.en} ${entry.es}`.toLowerCase();
      expect(blob).not.toMatch(/\bsurvey\b/);
      expect(blob).not.toMatch(/\bencuesta\b/);
      expect(blob).not.toMatch(/\brate (us|this)\b/);
      expect(entry.kind).not.toBe("survey" as ColdStartEntryKind);
    }
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
