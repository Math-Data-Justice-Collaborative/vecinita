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
      className="sticky top-0 z-40 border-b border-amber-500/40 bg-amber-500/15 px-3 py-1.5 text-center text-xs font-semibold text-amber-950 sm:px-4 sm:py-2 sm:text-sm dark:text-amber-100"
    >
      {message}
    </div>
  );
}
