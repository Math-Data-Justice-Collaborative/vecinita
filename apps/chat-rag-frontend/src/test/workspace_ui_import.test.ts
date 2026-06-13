import { describe, expect, it } from "vitest";

describe("workspace import: chat-rag-frontend → frontend-ui", () => {
  it("resolves vecinita-frontend-ui via npm workspace link", async () => {
    const ui = await import("vecinita-frontend-ui");
    expect(ui).toBeDefined();
  });
});
