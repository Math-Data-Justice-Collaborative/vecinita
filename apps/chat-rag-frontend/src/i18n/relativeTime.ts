import type { Locale } from "../hooks/useLocale.types";

type Division = { amount: number; unit: Intl.RelativeTimeFormatUnit };

const DIVISIONS: Division[] = [
  { amount: 60, unit: "second" },
  { amount: 60, unit: "minute" },
  { amount: 24, unit: "hour" },
  { amount: 7, unit: "day" },
  { amount: 4.34524, unit: "week" },
  { amount: 12, unit: "month" },
];

/**
 * Locale-aware relative timestamp (e.g. "2 hours ago" / "hace 2 horas") via
 * `Intl.RelativeTimeFormat`. Used to label previous conversations (RD-071).
 */
export function formatRelativeTime(
  timestamp: number,
  locale: Locale,
  now: number = Date.now(),
): string {
  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  let duration = (timestamp - now) / 1000;
  for (const division of DIVISIONS) {
    if (Math.abs(duration) < division.amount) {
      return formatter.format(Math.round(duration), division.unit);
    }
    duration /= division.amount;
  }
  return formatter.format(Math.round(duration), "year");
}
