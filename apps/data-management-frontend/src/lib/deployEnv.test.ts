import { describe, expect, it } from "vitest";

import { resolveDeployEnv } from "./deployEnv";

describe("resolveDeployEnv (F83 / EV-staging-adversarial-ux)", () => {
  it("honors explicit VITE_VECINITA_DEPLOY_ENV on non-staging hosts", () => {
    expect(resolveDeployEnv("anything.ondigitalocean.app", "staging")).toBe(
      "staging",
    );
    expect(resolveDeployEnv("anything.ondigitalocean.app", "production")).toBe(
      "production",
    );
    expect(resolveDeployEnv("app.example.com", "local")).toBe("local");
    expect(resolveDeployEnv("x", "STAGING")).toBe("staging");
  });

  it("staging hostname wins over mis-baked production flag", () => {
    expect(
      resolveDeployEnv(
        "vecinita-staging-admin-fe-4tj2p.ondigitalocean.app",
        "production",
      ),
    ).toBe("staging");
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
    expect(resolveDeployEnv("admin.local", "")).toBe("local");
  });

  it("treats non-staging hosts as production; empty host unknown", () => {
    expect(resolveDeployEnv("vecinita-chat-fe.ondigitalocean.app", "")).toBe(
      "production",
    );
    expect(resolveDeployEnv("", undefined)).toBe("unknown");
  });
});
