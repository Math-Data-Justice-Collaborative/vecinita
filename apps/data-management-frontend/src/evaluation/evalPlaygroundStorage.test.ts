import { afterEach, describe, expect, it } from "vitest";

import {
  loadEvalPlaygroundPreferences,
  saveEvalPlaygroundLastPresetId,
} from "./evalPlaygroundStorage";

const STORAGE_KEY = "vecinita.eval.playground.v1";
const PRESET_ID = "00000000-0000-0000-0000-0000000000aa";

describe("evalPlaygroundStorage", () => {
  afterEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it("returns defaults when storage is empty", () => {
    expect(loadEvalPlaygroundPreferences()).toEqual({ lastPresetId: null });
  });

  it("persists and reloads last preset id (RD-129)", () => {
    saveEvalPlaygroundLastPresetId(PRESET_ID);
    expect(loadEvalPlaygroundPreferences().lastPresetId).toBe(PRESET_ID);
  });

  it("clears last preset id when saved as null", () => {
    saveEvalPlaygroundLastPresetId(PRESET_ID);
    saveEvalPlaygroundLastPresetId(null);
    expect(loadEvalPlaygroundPreferences().lastPresetId).toBeNull();
  });

  it("returns defaults when storage JSON is invalid", () => {
    localStorage.setItem(STORAGE_KEY, "not-json");
    expect(loadEvalPlaygroundPreferences()).toEqual({ lastPresetId: null });
  });
});
