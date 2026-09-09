import { describe, expect, it } from "vitest";

import { resolveDeployEnv } from "./deployEnv";

describe("resolveDeployEnv (chat / F83)", () => {
  it("detects staging hostnames", () => {
    expect(
      resolveDeployEnv("vecinita-staging-chat-fe.ondigitalocean.app", ""),
    ).toBe("staging");
  });

  it("honors explicit env", () => {
    expect(resolveDeployEnv("localhost", "production")).toBe("production");
  });
});
