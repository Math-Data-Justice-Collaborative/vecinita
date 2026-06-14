import { vi } from "vitest";

/** Parse JSON object body from a mocked fetch call (RequestInit.body is always string here). */
export function mockFetchJsonBody(index = 0): Record<string, unknown> {
  const raw = vi.mocked(fetch).mock.calls.at(index)?.[1]?.body;
  if (typeof raw !== "string") {
    throw new Error("Expected fetch body to be a string");
  }
  const parsed: unknown = JSON.parse(raw);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Expected fetch body JSON object");
  }
  return parsed as Record<string, unknown>;
}

/** Request URL from a mocked fetch call as a string. */
export function mockFetchUrl(index = 0): string {
  const input = vi.mocked(fetch).mock.calls.at(index)?.[0];
  if (input === undefined) {
    throw new Error(`fetch mock call ${String(index)} missing URL`);
  }
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.href;
  }
  return input.url;
}
