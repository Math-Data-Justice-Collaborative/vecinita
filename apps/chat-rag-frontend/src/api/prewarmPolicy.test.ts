import { afterEach, describe, expect, it } from "vitest";

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
});
