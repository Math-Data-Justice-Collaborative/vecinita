function tryParseJsonObjectString(raw: string): Record<string, unknown> | null {
  const trimmed = raw.trim();
  if (!trimmed.startsWith('{') || !trimmed.endsWith('}')) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(trimmed);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    // Not JSON (e.g. Python repr) — caller keeps the raw string or continues.
  }
  return null;
}

export function extractAssistantTextFromPayload(payload: unknown): string {
  if (typeof payload === 'string') {
    const trimmed = payload.trim();
    const parsed = tryParseJsonObjectString(trimmed);
    if (parsed) {
      const nested = extractAssistantTextFromPayload(parsed);
      if (nested) {
        return nested;
      }
    }
    return trimmed;
  }

  if (!payload || typeof payload !== 'object') {
    return '';
  }

  const record = payload as Record<string, unknown>;

  if (typeof record.answer === 'string') {
    const trimmedAnswer = record.answer.trim();
    if (trimmedAnswer.length > 0) {
      const parsedAnswer = tryParseJsonObjectString(trimmedAnswer);
      if (parsedAnswer) {
        const fromStructured = extractAssistantTextFromPayload(parsedAnswer);
        if (fromStructured) {
          return fromStructured;
        }
      }
      return trimmedAnswer;
    }
  }

  const message = record.message;
  if (message && typeof message === 'object') {
    const content = (message as Record<string, unknown>).content;
    if (typeof content === 'string' && content.trim().length > 0) {
      return content.trim();
    }
  }

  if (typeof record.content === 'string' && record.content.trim().length > 0) {
    return record.content.trim();
  }

  if (typeof record.response === 'string' && record.response.trim().length > 0) {
    return record.response.trim();
  }

  return '';
}
