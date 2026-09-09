/** Deploy environment for operator banners (F83). */

export type DeployEnv = "staging" | "production" | "local" | "unknown";

/**
 * Resolve deploy env from hostname heuristics first for staging/local hosts,
 * then optional Vite flag. Staging hostnames must not be masked by a mis-baked
 * ``production`` build flag (F83 / UX-1).
 */
export function resolveDeployEnv(
  hostname: string,
  envVar: string | undefined,
): DeployEnv {
  const host = hostname.trim().toLowerCase();
  if (host.includes("staging")) {
    return "staging";
  }
  if (host === "localhost" || host === "127.0.0.1" || host.endsWith(".local")) {
    return "local";
  }
  const explicit = (envVar ?? "").trim().toLowerCase();
  if (
    explicit === "staging" ||
    explicit === "production" ||
    explicit === "local"
  ) {
    return explicit;
  }
  if (host.length === 0) {
    return "unknown";
  }
  return "production";
}
