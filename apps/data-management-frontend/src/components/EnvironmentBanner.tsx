import { t } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

import { resolveDeployEnv } from "@/lib/deployEnv";

type EnvironmentBannerProps = {
  hostname?: string;
  deployEnvVar?: string | undefined;
};

/**
 * Non-dismissible operator banner when running on staging or local (F83 / UX-1).
 * Hidden on production so public/prod operators are not alarmed.
 */
export function EnvironmentBanner({
  hostname,
  deployEnvVar,
}: EnvironmentBannerProps = {}) {
  const { locale } = useLocale();
  const env = resolveDeployEnv(
    hostname ?? (typeof window !== "undefined" ? window.location.hostname : ""),
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
      role="status"
      data-testid="environment-banner"
      data-env={env}
      className="border-b border-amber-500/40 bg-amber-500/15 px-4 py-2 text-center text-sm font-medium text-amber-950 dark:text-amber-100"
    >
      {message}
    </div>
  );
}
