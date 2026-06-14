import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";
import type { Source, StreamEvent } from "./types";

/** Keep in sync with `vecinita_shared_schemas.transient_http`. */
export const COLD_START_ASK_MAX_ATTEMPTS = 3;
export const COLD_START_ASK_RETRY_DELAY_MS = 2500;

const TRANSIENT_ASK_STATUSES = new Set([502, 503, 504]);

export class AskStreamError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "AskStreamError";
  }
}

function parseSseLine(line: string): StreamEvent | null {
  if (!line.startsWith("data: ")) {
    return null;
  }
  const payload = line.slice(6).trim();
  if (!payload) {
    return null;
  }
  return JSON.parse(payload) as StreamEvent;
}

function isTransientAskFailure(error: unknown, status?: number): boolean {
  if (error instanceof TypeError) {
    return true;
  }
  if (status !== undefined && TRANSIENT_ASK_STATUSES.has(status)) {
    return true;
  }
  return false;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function* streamAskOnce(
  question: string,
  baseUrl: string,
  options?: { tags?: string[]; language?: Locale },
): AsyncGenerator<StreamEvent> {
  const body: { question: string; tags?: string[]; language?: Locale } = {
    question,
  };
  if (options?.language) {
    body.language = options.language;
  }
  if (options?.tags && options.tags.length > 0) {
    body.tags = options.tags;
  }
  const response = await fetch(`${baseUrl}/api/v1/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new AskStreamError(
      detail || `Ask failed (${String(response.status)})`,
      response.status,
    );
  }
  if (!response.body) {
    throw new AskStreamError("No response body from ask/stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    const remainder = lines.pop();
    buffer = remainder === undefined ? "" : remainder;
    for (const line of lines) {
      const event = parseSseLine(line);
      if (event) {
        yield event;
      }
    }
  }

  if (buffer.trim()) {
    const event = parseSseLine(buffer.trim());
    if (event) {
      yield event;
    }
  }
}

export type StreamAskOptions = {
  tags?: string[];
  language?: Locale;
  onRetry?: (attempt: number, maxAttempts: number) => void;
};

/** Stream ask tokens and sources from POST /api/v1/ask/stream (F2). */
export async function* streamAsk(
  question: string,
  baseUrl: string,
  options?: StreamAskOptions,
): AsyncGenerator<StreamEvent> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= COLD_START_ASK_MAX_ATTEMPTS; attempt++) {
    try {
      yield* streamAskOnce(question, baseUrl, {
        tags: options?.tags,
        language: options?.language,
      });
      return;
    } catch (err) {
      const status = err instanceof AskStreamError ? err.status : undefined;
      if (
        !isTransientAskFailure(err, status) ||
        attempt === COLD_START_ASK_MAX_ATTEMPTS
      ) {
        throw err;
      }
      options?.onRetry?.(attempt, COLD_START_ASK_MAX_ATTEMPTS);
      await sleep(COLD_START_ASK_RETRY_DELAY_MS);
      lastError = err instanceof Error ? err : new Error(String(err));
    }
  }

  throw lastError ?? new AskStreamError("Ask failed");
}

export function isTokenEvent(event: StreamEvent): event is { token: string } {
  return "token" in event;
}

export function isSourcesEvent(
  event: StreamEvent,
): event is { sources: Source[] } {
  return "sources" in event;
}

export function isDoneEvent(event: StreamEvent): event is { done: true } {
  return "done" in event;
}

/** User-facing message when all cold-start retries are exhausted. */
export function formatAskFailureMessage(
  error: unknown,
  locale: Locale,
): string {
  if (error instanceof AskStreamError && error.status !== undefined) {
    if (TRANSIENT_ASK_STATUSES.has(error.status)) {
      return t(locale, "askStillStarting");
    }
    if (error.status === 401 || error.status === 403) {
      return t(locale, "askUnauthorized");
    }
    if (error.status >= 500) {
      return t(locale, "askServerError");
    }
    return t(locale, "requestFailed");
  }
  if (error instanceof TypeError) {
    return t(locale, "askStartingWait");
  }
  if (error instanceof Error) {
    return t(locale, "requestFailed");
  }
  return t(locale, "requestFailed");
}
