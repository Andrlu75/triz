/** Formatting helpers used across the application. */

/**
 * Format an ISO date string as a localized Russian date.
 *
 * @example formatDate("2024-06-15T10:00:00Z") → "15 июня 2024 г."
 */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/**
 * Format an ISO date string as a short Russian date (DD.MM.YYYY).
 *
 * @example formatDateShort("2024-06-15T10:00:00Z") → "15.06.2024"
 */
export function formatDateShort(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU");
}

/**
 * Format an ISO date string as a relative "time ago" string in Russian.
 *
 * @example formatTimeAgo("...") → "5 минут назад"
 */
export function formatTimeAgo(iso: string): string {
  const now = Date.now();
  const diff = now - new Date(iso).getTime();
  const seconds = Math.floor(diff / 1000);

  if (seconds < 60) return "только что";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} ${pluralize(minutes, "минуту", "минуты", "минут")} назад`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} ${pluralize(hours, "час", "часа", "часов")} назад`;
  }

  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days} ${pluralize(days, "день", "дня", "дней")} назад`;
  }

  return formatDateShort(iso);
}

/**
 * Russian pluralization helper.
 *
 * @param n - number to pluralize for
 * @param one - form for 1 (минута)
 * @param few - form for 2-4 (минуты)
 * @param many - form for 5-20 (минут)
 */
export function pluralize(
  n: number,
  one: string,
  few: string,
  many: string,
): string {
  const abs = Math.abs(n) % 100;
  const lastDigit = abs % 10;

  if (abs >= 11 && abs <= 19) return many;
  if (lastDigit === 1) return one;
  if (lastDigit >= 2 && lastDigit <= 4) return few;
  return many;
}

/**
 * Format a progress percentage (0-100) as a string with one decimal place.
 *
 * @example formatPercent(66.667) → "66.7%"
 */
export function formatPercent(value: number): string {
  return `${Math.round(value * 10) / 10}%`;
}

/**
 * Truncate a string to a maximum length, appending an ellipsis if truncated.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + "\u2026";
}
