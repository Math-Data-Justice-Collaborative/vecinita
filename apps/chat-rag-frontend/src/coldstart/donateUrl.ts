import { DEFAULT_WRWC_DONATE_URL } from "./constants";

/** Resolve donate CTA href (optional `VITE_WRWC_DONATE_URL`). */
export function resolveDonateUrl(
  envDonateUrl: string | undefined = import.meta.env.VITE_WRWC_DONATE_URL,
): string {
  const trimmed = envDonateUrl?.trim();
  if (!trimmed) {
    return DEFAULT_WRWC_DONATE_URL;
  }
  return trimmed.endsWith("/") ? trimmed : `${trimmed}/`;
}
