import type { Locale } from "./locale";

/** Stub — implementation in T33.2. */
export function t(
  _locale: Locale,
  _key: string,
  ..._args: number[]
): string {
  throw new Error("t() not implemented");
}
