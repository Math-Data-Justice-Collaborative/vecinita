import { describe, expect, it } from "vitest";

import { resolveDeployEnv } from "./deployEnv";

describe("resolveDeployEnv (F83 / EV-staging-adversarial-ux)", () => {
  it("honors explicit VITE_VECINITA_DEPLOY_ENV", () => {
    expect(resolveDeployEnv("anything.ondigitalocean.app", "staging")).toBe(
      "staging",
    );
    expect(resolveDeployEnv("anything.ondigitalocean.app", "production")).toBe(
      "production",
    );
    expect(resolveDeployEnv("staging.example.com", "local")).toBe("local");
  });

  it("detects staging from hostname when env unset", () => {
    expect(
      resolveDeployEnv(
        "vecinita-staging-admin-fe-4tj2p.ondigitalocean.app",
        "",
      ),
    ).toBe("staging");
    expect(
      resolveDeployEnv(
        "vecinita-staging-chat-fe-epvwo.ondigitalocean.app",
        undefined,
      ),
    ).toBe("staging");
  });

  it("detects local hostnames", () => {
    expect(resolveDeployEnv("localhost", undefined)).toBe("local");
    expect(resolveDeployEnv("127.0.0.1", "")).toBe("local");
  });

  it("treats non-staging DigitalOcean hosts as production", () => {
    expect(resolveDeployEnv("vecinita-chat-fe.ondigitalocean.app", "")).toBe(
      "production",
    );
  });
});
