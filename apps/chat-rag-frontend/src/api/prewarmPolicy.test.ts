import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PREWARM_POLICY_STORAGE_KEY,
  readPrewarmPolicyEvidence,
  recordAskStarted,
  recordPrewarmRequested,
} from "./prewarmPolicy";

describe("prewarm trigger-policy evidence", () => {
  afterEach(() => {
    sessionStorage.clear();
  });

  it("records privacy-safe mount counters without storing prompt text", () => {
    recordPrewarmRequested("mount");
    recordAskStarted();

    const raw = sessionStorage.getItem(PREWARM_POLICY_STORAGE_KEY);
    expect(raw).not.toBeNull();
    expect(raw).not.toContain("Where is the pantry?");
    expect(raw).not.toContain("question");
    expect(raw).not.toContain("answer");

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 1,
      ask_started: 1,
      prewarm_to_ask_hit_rate: 1,
      policies: {
        mount: {
          prewarm_requested: 1,
          ask_started: 1,
          prewarm_to_ask_hit_rate: 1,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("counts only one ask hit per pending prewarm request", () => {
    recordPrewarmRequested("mount");
    recordAskStarted();
    recordAskStarted();

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 1,
      ask_started: 2,
      prewarm_to_ask_hit_rate: 1,
      policies: {
        mount: {
          prewarm_requested: 1,
          ask_started: 1,
          prewarm_to_ask_hit_rate: 1,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("falls back to an empty envelope when stored JSON is malformed", () => {
    sessionStorage.setItem(PREWARM_POLICY_STORAGE_KEY, "{not-json");

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("falls back to an empty envelope when stored JSON is not an object", () => {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify("not-an-object"),
    );

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("falls back to an empty envelope when policy counters are invalid", () => {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        prewarm_requested: 1,
        ask_started: 0,
        pending_policy: "mount",
        policies: {
          mount: { prewarm_requested: "bad", ask_started: 0 },
          dwell: { prewarm_requested: 0, ask_started: 0 },
          focus: { prewarm_requested: 0, ask_started: 0 },
          "first-keystroke": { prewarm_requested: 0, ask_started: 0 },
        },
      }),
    );

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("falls back to an empty envelope when a policy entry is not an object", () => {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        prewarm_requested: 1,
        ask_started: 0,
        pending_policy: "mount",
        policies: {
          mount: null,
          dwell: { prewarm_requested: 0, ask_started: 0 },
          focus: { prewarm_requested: 0, ask_started: 0 },
          "first-keystroke": { prewarm_requested: 0, ask_started: 0 },
        },
      }),
    );

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("falls back to an empty envelope when the top-level shape is invalid", () => {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify({
        version: 2,
        prewarm_requested: 1,
        ask_started: 0,
      }),
    );

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("ignores an invalid pending policy while preserving valid counters", () => {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        prewarm_requested: 2,
        ask_started: 1,
        pending_policy: "hover",
        policies: {
          mount: { prewarm_requested: 1, ask_started: 1 },
          dwell: { prewarm_requested: 1, ask_started: 0 },
          focus: { prewarm_requested: 0, ask_started: 0 },
          "first-keystroke": { prewarm_requested: 0, ask_started: 0 },
        },
      }),
    );

    recordAskStarted();

    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 2,
      ask_started: 2,
      prewarm_to_ask_hit_rate: 1,
      policies: {
        mount: {
          prewarm_requested: 1,
          ask_started: 1,
          prewarm_to_ask_hit_rate: 1,
        },
        dwell: {
          prewarm_requested: 1,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });
  });

  it("tolerates unavailable storage APIs", () => {
    const getItem = vi
      .spyOn(Storage.prototype, "getItem")
      .mockImplementation(() => {
        throw new Error("blocked");
      });
    const setItem = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("blocked");
      });

    expect(() => {
      recordPrewarmRequested("focus");
    }).not.toThrow();
    expect(() => {
      recordAskStarted();
    }).not.toThrow();
    expect(readPrewarmPolicyEvidence()).toEqual({
      version: 1,
      prewarm_requested: 0,
      ask_started: 0,
      prewarm_to_ask_hit_rate: 0,
      policies: {
        mount: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        dwell: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        focus: {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
        "first-keystroke": {
          prewarm_requested: 0,
          ask_started: 0,
          prewarm_to_ask_hit_rate: 0,
        },
      },
    });

    getItem.mockRestore();
    setItem.mockRestore();
  });
});
