import type { SessionProgress } from "@/api/types";

interface StepProgressProps {
  progress: SessionProgress;
  onStepClick?: (code: string) => void;
}

export default function StepProgress({
  progress,
  onStepClick,
}: StepProgressProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Прогресс
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {progress.completed_count}/{progress.total_steps} ({progress.percent}%)
        </span>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-4">
        <div
          className="bg-primary-600 h-1.5 rounded-full transition-all"
          style={{ width: `${progress.percent}%` }}
        />
      </div>

      <div className="space-y-1">
        {progress.steps_completed.map((step) => {
          const isCurrent = step.code === progress.current_step;
          const isCompleted = step.completed;

          return (
            <button
              key={step.code}
              onClick={() => isCompleted && onStepClick?.(step.code)}
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
                {isCompleted ? "\u2713" : step.code}
              </span>
              <span className="truncate">{step.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
