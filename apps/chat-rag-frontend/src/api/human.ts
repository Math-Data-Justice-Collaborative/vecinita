/**
 * F-HUMAN "are you human?" check (Cloudflare Turnstile).
 *
 * The backend says whether the check is on (GET /api/v1/human/config). When it
 * is, the widget token is exchanged for a short-lived human pass
 * (POST /api/v1/human/verify) that rides on ask requests as `X-Human-Pass`.
 * The pass lives in memory only — never localStorage — and carries no personal data.
 */

export const HUMAN_PASS_HEADER = "X-Human-Pass";

/** Refresh a little early so a pass never expires mid-request. */
const PASS_EXPIRY_MARGIN_S = 30;

export type HumanVerificationConfig = {
  enabled: boolean;
  provider: "turnstile";
  site_key: string;
};

type HumanPass = { token: string; expiresAt: number };

let currentPass: HumanPass | null = null;

export function setHumanPass(token: string, expiresAt: number): void {
  currentPass = { token, expiresAt };
}

export function clearHumanPass(): void {
  currentPass = null;
}

/** Valid (unexpired) pass token, or null when the visitor must re-check. */
export function getHumanPass(nowMs: number = Date.now()): string | null {
  if (!currentPass) {
    return null;
  }
  if (currentPass.expiresAt - PASS_EXPIRY_MARGIN_S <= nowMs / 1000) {
    currentPass = null;
    return null;
  }
  return currentPass.token;
}

const DISABLED: HumanVerificationConfig = {
  enabled: false,
  provider: "turnstile",
  site_key: "",
};

/** Read the public F-HUMAN config. Older backends without the route → disabled. */
export async function fetchHumanConfig(
  baseUrl: string,
): Promise<HumanVerificationConfig> {
  try {
    const response = await fetch(`${baseUrl}/api/v1/human/config`);
    if (!response.ok) {
      return DISABLED;
    }
    const body = (await response.json()) as Partial<HumanVerificationConfig>;
    return {
      enabled: body.enabled === true && Boolean(body.site_key),
      provider: "turnstile",
      site_key: body.site_key ?? "",
    };
  } catch {
    return DISABLED;
  }
}

/** Exchange a Turnstile widget token for a human pass; stores it on success. */
export async function verifyHuman(
  baseUrl: string,
  widgetToken: string,
): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}/api/v1/human/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: widgetToken }),
    });
    if (!response.ok) {
      return false;
    }
    const body = (await response.json()) as {
      human_pass?: string;
      expires_at?: number;
    };
    if (!body.human_pass || typeof body.expires_at !== "number") {
      return false;
    }
    setHumanPass(body.human_pass, body.expires_at);
    return true;
  } catch {
    return false;
  }
}
