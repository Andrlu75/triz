import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import type { StepResult } from "@/api/types";

interface LLMResponseProps {
  step: StepResult;
}

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  completed: {
    label: "Готово",
    className: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  },
  failed: {
    label: "Ошибка",
    className: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  },
  pending: {
    label: "Ожидание",
    className: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  },
  in_progress: {
    label: "В обработке",
    className: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  },
};

export default function LLMResponse({ step }: LLMResponseProps) {
  const content = step.validated_result || step.llm_output;
  const badge = STATUS_BADGES[step.status] || STATUS_BADGES.pending;

  if (!content) return null;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          {step.step_name}
        </span>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge.className}`}
        >
          {badge.label}
        </span>
      </div>
      <MarkdownRenderer content={content} />
      {step.validation_notes && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {step.validation_notes}
          </p>
        </div>
      )}
    </div>
  );
}
