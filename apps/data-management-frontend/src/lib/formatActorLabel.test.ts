import { describe, expect, it } from "vitest";

import { formatActorLabel } from "./formatActorLabel";

const ACTOR_ID = "11111111-1111-1111-1111-111111111111";

describe("formatActorLabel (F69 / UJ-074)", () => {
  it("prefers actor_email when present", () => {
    expect(formatActorLabel("operator@example.com", ACTOR_ID)).toBe(
      "operator@example.com",
    );
  });

  it("falls back to truncated actor_id when email is null", () => {
    expect(formatActorLabel(null, ACTOR_ID)).toBe("11111111…");
  });

  it("falls back when email is empty/whitespace", () => {
    expect(formatActorLabel("  ", ACTOR_ID)).toBe("11111111…");
  });

  it("returns em dash when both missing", () => {
    expect(formatActorLabel(null, null)).toBe("—");
    expect(formatActorLabel(undefined, undefined)).toBe("—");
  });

  it("returns short actor_id unchanged", () => {
    expect(formatActorLabel(null, "abc")).toBe("abc");
  });
});
