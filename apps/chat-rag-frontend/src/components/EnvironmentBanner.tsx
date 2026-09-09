import { t } from "vecinita-frontend-i18n";

import type { Locale } from "../hooks/useLocale.types";
import { resolveDeployEnv } from "../lib/deployEnv";

type EnvironmentBannerProps = {
  locale: Locale;
  hostname?: string;
  deployEnvVar?: string | undefined;
};

/** Staging/local operator banner for ChatRAG (UX-1 / F83). */
export function EnvironmentBanner({
  locale,
  hostname,
  deployEnvVar,
}: EnvironmentBannerProps) {
  const env = resolveDeployEnv(
    hostname ?? window.location.hostname,
    deployEnvVar !== undefined
      ? deployEnvVar
      : (import.meta.env["VITE_VECINITA_DEPLOY_ENV"] as string | undefined),
  );

  if (env !== "staging" && env !== "local") {
    return null;
  }

  const message =
    env === "staging"
      ? t(locale, "shared.envBanner.staging")
      : t(locale, "shared.envBanner.local");

  return (
    <div
      role="region"
      aria-label={t(locale, "shared.envBanner.regionLabel")}
      data-testid="environment-banner"
      data-env={env}
      className="environment-banner"
    >
      {message}
    </div>
  );
}
