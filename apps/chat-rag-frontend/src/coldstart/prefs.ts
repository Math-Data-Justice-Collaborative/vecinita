import {
  COLD_START_CONSENT_COOKIE,
  COLD_START_CONSENT_MAX_AGE_SECONDS,
  COLD_START_FACTS_STORAGE_KEY,
} from "./constants";

export type ColdStartConsent = "accept" | "opt_out" | null;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const trimmed = part.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length));
    }
  }
  return null;
}

function writeCookie(name: string, value: string): void {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = [
    `${name}=${encodeURIComponent(value)}`,
    "Path=/",
    "SameSite=Lax",
    `Max-Age=${String(COLD_START_CONSENT_MAX_AGE_SECONDS)}`,
  ].join("; ");
}

export function getColdStartConsent(): ColdStartConsent {
  const raw = readCookie(COLD_START_CONSENT_COOKIE);
  if (raw === "1") {
    return "accept";
  }
  if (raw === "0") {
    return "opt_out";
  }
  return null;
}

export function setColdStartConsent(consent: "accept" | "opt_out"): void {
  writeCookie(COLD_START_CONSENT_COOKIE, consent === "accept" ? "1" : "0");
  if (consent === "opt_out") {
    clearSeenFactIds();
  }
}

export function getSeenFactIds(): string[] {
  try {
    const raw = localStorage.getItem(COLD_START_FACTS_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((id): id is string => typeof id === "string");
  } catch {
    return [];
  }
}

export function rememberSeenFactId(factId: string): void {
  if (getColdStartConsent() !== "accept") {
    return;
  }
  const current = getSeenFactIds();
  if (current.includes(factId)) {
    return;
  }
  try {
    localStorage.setItem(
      COLD_START_FACTS_STORAGE_KEY,
      JSON.stringify([...current, factId]),
    );
  } catch {
    // Quota / private mode — degrade without throwing (ADR-039).
  }
}

export function clearSeenFactIds(): void {
  try {
    localStorage.removeItem(COLD_START_FACTS_STORAGE_KEY);
  } catch {
    // ignore
  }
}
