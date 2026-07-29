/** F40 / EV-014 cold-start wait UX constants (ADR-039, config-spec). */

export const COLD_START_FACTS_STORAGE_KEY = "vecinita.chat.coldstart.facts.v1";

export const COLD_START_CONSENT_COOKIE = "vecinita_chat_coldstart_consent";

/** Max-Age = 1 year (Gate A→B M1). */
export const COLD_START_CONSENT_MAX_AGE_SECONDS = 31_536_000;

/** Rotate fun facts every ~4–5s (RD-186). */
export const FACT_ROTATION_MS = 4_500;

/** Show wait UX after this delay with no first token (S016-D7). */
export const SLOW_STREAM_WAIT_MS = 8_000;

export const DEFAULT_WRWC_DONATE_URL = "https://wrwc.org/donate/";
