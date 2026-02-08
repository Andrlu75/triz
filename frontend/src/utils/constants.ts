/** Application-wide constants. */

export const APP_NAME = "ТРИЗ-Решатель";

/** Human-readable labels for problem modes. */
export const MODE_LABELS: Record<string, string> = {
  express: "Экспресс",
  full: "Полный АРИЗ-2010",
  autopilot: "Автопилот",
};

/** Human-readable labels for problem statuses. */
export const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  in_progress: "В работе",
  completed: "Завершена",
  archived: "Архив",
};

/** Human-readable labels for problem domains. */
export const DOMAIN_LABELS: Record<string, string> = {
  technical: "Техническая",
  business: "Бизнес",
  everyday: "Бытовая",
};

/** Tailwind color classes for problem statuses. */
export const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  in_progress:
    "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  completed:
    "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  archived:
    "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
};

/** Session status labels. */
export const SESSION_STATUS_LABELS: Record<string, string> = {
  active: "Активна",
  completed: "Завершена",
  abandoned: "Отменена",
};

/** Polling configuration for Celery task status checks. */
export const POLLING = {
  /** Initial interval in milliseconds. */
  INITIAL_INTERVAL_MS: 1000,
  /** Maximum interval in milliseconds (after backoff). */
  MAX_INTERVAL_MS: 3000,
  /** Backoff multiplier applied on each poll. */
  BACKOFF_FACTOR: 1.5,
  /** Maximum number of retries before giving up. */
  MAX_RETRIES: 120,
} as const;
