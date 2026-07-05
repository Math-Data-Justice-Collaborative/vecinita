const STORAGE_KEY = "vecinita.eval.playground.v1";

export interface EvalPlaygroundPreferences {
  lastPresetId: string | null;
}

const DEFAULT_PREFERENCES: EvalPlaygroundPreferences = {
  lastPresetId: null,
};

export function loadEvalPlaygroundPreferences(): EvalPlaygroundPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    const parsed = JSON.parse(raw) as Partial<EvalPlaygroundPreferences>;
    return {
      lastPresetId:
        typeof parsed.lastPresetId === "string" ? parsed.lastPresetId : null,
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function saveEvalPlaygroundLastPresetId(presetId: string | null): void {
  try {
    const current = loadEvalPlaygroundPreferences();
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...current, lastPresetId: presetId }),
    );
  } catch {
    // degrade silently per ADR-004 localStorage policy
  }
}
