/**
 * Citation URL helpers for ChatRAG SourceList (F72 / EV-026).
 * Display filter only — does not reject ingest or backend storage.
 */

function trimmedUrl(url: string | null | undefined): string | null {
  if (url == null) {
    return null;
  }
  const trimmed = url.trim();
  return trimmed.length === 0 ? null : trimmed;
}

/**
 * True only for absolute `http:` / `https:` URLs (AC-SU1).
 */
export function isSafeHttpUrl(url: string | null | undefined): boolean {
  const value = trimmedUrl(url);
  if (value === null) {
    return false;
  }
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

/**
 * Returns the href string when safe; otherwise `null` (plain-text title path).
 */
export function citationHref(url: string | null | undefined): string | null {
  const value = trimmedUrl(url);
  if (value === null || !isSafeHttpUrl(value)) {
    return null;
  }
  return value;
}
