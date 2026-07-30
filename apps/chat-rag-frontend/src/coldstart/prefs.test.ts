import { afterEach, describe, expect, it } from "vitest";

import {
  COLD_START_CONSENT_COOKIE,
  COLD_START_CONSENT_MAX_AGE_SECONDS,
  COLD_START_FACTS_STORAGE_KEY,
} from "./constants";
import {
  clearSeenFactIds,
  getColdStartConsent,
  getSeenFactIds,
  rememberSeenFactId,
  setColdStartConsent,
} from "./prefs";

describe("coldstart prefs (TC-158 / ADR-039)", () => {
  afterEach(() => {
    document.cookie = `${COLD_START_CONSENT_COOKIE}=; Path=/; Max-Age=0`;
    localStorage.removeItem(COLD_START_FACTS_STORAGE_KEY);
  });

  it("returns null consent when cookie unset", () => {
    expect(getColdStartConsent()).toBeNull();
  });

  it("Accept sets consent cookie with 1-year Max-Age and allows seen ids", () => {
    setColdStartConsent("accept");
    expect(getColdStartConsent()).toBe("accept");
    expect(document.cookie).toContain(`${COLD_START_CONSENT_COOKIE}=1`);
    expect(COLD_START_CONSENT_MAX_AGE_SECONDS).toBe(31_536_000);

    rememberSeenFactId("heritage-river");
    expect(getSeenFactIds()).toEqual(["heritage-river"]);
  });

  it("Opt-out sets cookie 0 and does not persist seen ids", () => {
    setColdStartConsent("opt_out");
    expect(getColdStartConsent()).toBe("opt_out");
    expect(document.cookie).toContain(`${COLD_START_CONSENT_COOKIE}=0`);

    rememberSeenFactId("heritage-river");
    expect(getSeenFactIds()).toEqual([]);
  });

  it("opt-out clears previously stored seen ids", () => {
    setColdStartConsent("accept");
    rememberSeenFactId("waterfire");
    expect(getSeenFactIds()).toEqual(["waterfire"]);

    setColdStartConsent("opt_out");
    expect(getSeenFactIds()).toEqual([]);
  });

  it("clearSeenFactIds removes storage key", () => {
    setColdStartConsent("accept");
    rememberSeenFactId("what-cheer");
    clearSeenFactIds();
    expect(getSeenFactIds()).toEqual([]);
  });
});
