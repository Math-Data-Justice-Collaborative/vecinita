import type { Locale } from "./locale";
import {
  paginationMessages,
  stringMessages,
  type MessageKey,
  type StringMessageKey,
} from "./messages";

export type { MessageKey, StringMessageKey };

function applyParams(
  template: string,
  params?: Record<string, string | number>,
): string {
  if (!params) {
    return template;
  }
  return Object.entries(params).reduce(
    (result, [key, value]) => result.replaceAll(`{${key}}`, String(value)),
    template,
  );
}

export function t(
  locale: Locale,
  key: Exclude<MessageKey, "shared.pagination">,
  params?: Record<string, string | number>,
): string;
export function t(
  locale: Locale,
  key: "shared.pagination",
  page: number,
  totalPages: number,
  total: number,
): string;
export function t(
  locale: Locale,
  key: MessageKey,
  arg2?: number | Record<string, string | number>,
  arg3?: number,
  arg4?: number,
): string {
  if (key === "shared.pagination") {
    const page = typeof arg2 === "number" ? arg2 : 1;
    const totalPages = typeof arg3 === "number" ? arg3 : 1;
    const total = typeof arg4 === "number" ? arg4 : 0;
    return paginationMessages[locale](page, totalPages, total);
  }

  const params =
    arg2 !== undefined && typeof arg2 === "object" ? arg2 : undefined;
  return applyParams(stringMessages[locale][key], params);
}
