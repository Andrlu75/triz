import { useState } from "react";
import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import type { StepResult } from "@/api/types";

interface LLMResponseProps {
  step: StepResult;
}

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  completed: {
    label: "Готово",
    className:
      "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  },
  failed: {
    label: "Ошибка",
    className:
      "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
  },
  pending: {
    label: "Ожидание",
    className:
      "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  },
  in_progress: {
    label: "В обработке",
    className:
      "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  },
};

/**
 * Card displaying an LLM response with Markdown rendering.
 *
 * Shows:
 * - Step name as a subtle label
 * - Status badge (completed, failed, etc.)
 * - Validated result (preferred) or raw LLM output
 * - Expandable validation notes (if present)
 */
export default function LLMResponse({ step }: LLMResponseProps) {
  const [notesExpanded, setNotesExpanded] = useState(false);

  const content = step.validated_result || step.llm_output;
  const badge = STATUS_BADGES[step.status] || STATUS_BADGES.pending;

  if (!content) return null;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 animate-fade-in">
      {/* Header: step name + status badge */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-semibold">
            {step.step_code}
          </span>
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {step.step_name}
          </span>
        </div>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge.className}`}
        >
          {badge.label}
        </span>
      </div>

      {/* Content */}
      <MarkdownRenderer content={content} />

      {/* Validation notes (expandable) */}
      {step.validation_notes && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <button
            onClick={() => setNotesExpanded(!notesExpanded)}
            className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <svg
              className={`h-3.5 w-3.5 transition-transform ${notesExpanded ? "rotate-90" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
            Заметки валидации
          </button>
          {notesExpanded && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 leading-relaxed whitespace-pre-wrap">
              {step.validation_notes}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
