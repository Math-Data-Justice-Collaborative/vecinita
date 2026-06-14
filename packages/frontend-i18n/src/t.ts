import type { Locale } from "./locale";

/** TC-067 sample keys; full map in T33.2 (ADR-021 TP-032). */
export type MessageKey =
  | "shared.pagination"
  | "shared.previous"
  | "shared.next"
  | "chat.ask";

/** Stub — implementation in T33.2. */
export function t(
  _locale: Locale,
  _key: MessageKey,
  ..._args: number[]
): string {
  throw new Error("t() not implemented");
}
