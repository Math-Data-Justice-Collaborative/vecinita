/** Deploy environment for operator banners (F83). */

export type DeployEnv = "staging" | "production" | "local" | "unknown";

/**
 * Resolve deploy env from optional Vite flag, else hostname heuristics.
 */
export function resolveDeployEnv(
  hostname: string,
  envVar: string | undefined,
): DeployEnv {
  const explicit = (envVar ?? "").trim().toLowerCase();
  if (
    explicit === "staging" ||
    explicit === "production" ||
    explicit === "local"
  ) {
    return explicit;
  }
  const host = hostname.trim().toLowerCase();
  if (host.includes("staging")) {
    return "staging";
  }
  if (host === "localhost" || host === "127.0.0.1" || host.endsWith(".local")) {
    return "local";
  }
  if (host.length === 0) {
    return "unknown";
  }
  return "production";
}
