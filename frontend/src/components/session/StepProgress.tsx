import { useState } from "react";
import type { SessionProgress } from "@/api/types";

interface StepProgressProps {
  progress: SessionProgress;
  onStepClick?: (code: string) => void;
  /** Collapsed horizontal mode for mobile. */
  compact?: boolean;
}

/**
 * Vertical progress bar showing ARIZ steps.
 *
 * - Current step is highlighted in primary color
 * - Completed steps are green with a checkmark
 * - Clickable completed steps trigger `onStepClick`
 * - When `compact` is true, renders a minimal horizontal bar for mobile
 */
export default function StepProgress({
  progress,
  onStepClick,
  compact = false,
}: StepProgressProps) {
  const [expanded, setExpanded] = useState(false);

  // -------------------------------------------------------------------------
  // Compact / mobile view: horizontal bar + expandable list
  // -------------------------------------------------------------------------
  if (compact) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-3">
        {/* Clickable header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Шаг {progress.current_step}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {progress.current_step_name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {progress.completed_count}/{progress.total_steps}
            </span>
            <svg
              className={`h-4 w-4 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </button>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-2">
          <div
            className="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${progress.percent}%` }}
          />
        </div>

        {/* Expandable step list */}
        {expanded && (
          <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-800 space-y-1">
            {progress.steps_completed.map((step) => (
              <StepItem
                key={step.code}
                step={step}
                isCurrent={step.code === progress.current_step}
                onClick={onStepClick}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Full desktop view: vertical list
  // -------------------------------------------------------------------------
  return (
    <div className="space-y-1">
      {/* Header with progress summary */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Прогресс
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {progress.completed_count}/{progress.total_steps} ({progress.percent}%)
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-4">
        <div
          className="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${progress.percent}%` }}
        />
      </div>

      {/* Step list */}
      <div className="space-y-1">
        {progress.steps_completed.map((step) => (
          <StepItem
            key={step.code}
            step={step}
            isCurrent={step.code === progress.current_step}
            onClick={onStepClick}
          />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Internal StepItem component
// ---------------------------------------------------------------------------

interface StepItemProps {
  step: { code: string; name: string; completed: boolean };
  isCurrent: boolean;
  onClick?: (code: string) => void;
}

function StepItem({ step, isCurrent, onClick }: StepItemProps) {
  const isCompleted = step.completed;

  return (
    <button
      onClick={() => isCompleted && onClick?.(step.code)}
      disabled={!isCompleted}
      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 ${
        isCurrent
          ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 font-medium"
          : isCompleted
            ? "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            : "text-gray-400 dark:text-gray-600 cursor-default"
      }`}
    >
      <span
        className={`w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${
          isCompleted
            ? "bg-green-500 text-white"
            : isCurrent
              ? "bg-primary-500 text-white"
              : "bg-gray-200 dark:bg-gray-700 text-gray-400"
        }`}
      >
        {isCompleted ? (
          <svg
            className="h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={3}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        ) : (
          step.code
        )}
      </span>
      <span className="truncate">{step.name}</span>
    </button>
  );
}
