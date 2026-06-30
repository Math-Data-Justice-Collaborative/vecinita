/** Build-time config per docs/config-spec.md (VITE_VECINITA_*). */

export const adminApiUrl = import.meta.env.VITE_VECINITA_ADMIN_API_URL;
export const modalProxyKey = import.meta.env.VITE_VECINITA_MODAL_PROXY_KEY;
export const corpusApiUrl = import.meta.env.VITE_VECINITA_CORPUS_API_URL;
export const corpusApiKey = import.meta.env.VITE_VECINITA_CORPUS_API_KEY;
export const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
export const supabasePublishableKey = import.meta.env
  .VITE_SUPABASE_PUBLISHABLE_KEY;

function parsePositiveInt(raw: string | undefined, fallback: number): number {
  const parsed = Number(raw ?? fallback);
  return Number.isFinite(parsed) && parsed >= 1 ? Math.floor(parsed) : fallback;
}

/** Idle auto-logout minutes (UJ-034, TP-S005-17). */
export function idleTimeoutMinutes(): number {
  return parsePositiveInt(import.meta.env.VITE_VECINITA_IDLE_TIMEOUT_MIN, 30);
}

/** Idle warning countdown seconds before local sign-out (TP-S005-17). */
export function idleWarningSeconds(): number {
  return parsePositiveInt(import.meta.env.VITE_VECINITA_IDLE_WARNING_SEC, 60);
}

let operatorAccessToken: string | null = null;

/** Set by AuthProvider when the Supabase session changes (F34). */
export function setOperatorAccessToken(token: string | null): void {
  operatorAccessToken = token;
}

export function requireAdminConfig(): {
  baseUrl: string;
  modalKey: string;
  accessToken?: string | undefined;
} {
  if (!adminApiUrl || !modalProxyKey) {
    throw new Error(
      "Set VITE_VECINITA_ADMIN_API_URL and VITE_VECINITA_MODAL_PROXY_KEY (see .env.example)",
    );
  }
  return {
    baseUrl: adminApiUrl.replace(/\/$/, ""),
    modalKey: modalProxyKey,
    accessToken: operatorAccessToken ?? undefined,
  };
}

export function requireCorpusConfig(): {
  baseUrl: string;
  apiKey?: string | undefined;
  accessToken?: string | undefined;
} {
  if (!corpusApiUrl) {
    throw new Error("Set VITE_VECINITA_CORPUS_API_URL (see .env.example)");
  }
  const token = operatorAccessToken ?? undefined;
  if (!token && !corpusApiKey) {
    throw new Error(
      "Set VITE_VECINITA_CORPUS_API_KEY or sign in with Supabase (see .env.example)",
    );
  }
  return {
    baseUrl: corpusApiUrl.replace(/\/$/, ""),
    apiKey: corpusApiKey,
    accessToken: token,
  };
}
