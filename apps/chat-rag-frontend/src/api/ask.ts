import type { Source, StreamEvent } from "./types";

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

/** Stream ask tokens and sources from POST /api/v1/ask/stream (F2). */
export async function* streamAsk(
  question: string,
  baseUrl: string,
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${baseUrl}/api/v1/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Ask failed (${response.status})`);
  }
  if (!response.body) {
    throw new Error("No response body from ask/stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
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

export function isTokenEvent(event: StreamEvent): event is { token: string } {
  return "token" in event;
}

export function isSourcesEvent(event: StreamEvent): event is { sources: Source[] } {
  return "sources" in event;
}

export function isDoneEvent(event: StreamEvent): event is { done: true } {
  return "done" in event;
}
