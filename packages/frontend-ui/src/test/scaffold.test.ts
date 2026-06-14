import { describe, expect, it } from "vitest";

describe("frontend-ui package scaffold", () => {
  it("exports a stub module", async () => {
    const ui = await import("../index");
    expect(ui).toBeDefined();
  });
});
