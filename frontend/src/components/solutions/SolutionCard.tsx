import type { Solution } from "@/api/types";

interface SolutionCardProps {
  solution: Solution;
}

const METHOD_LABELS: Record<string, string> = {
  principle: "Приём",
  standard: "Стандарт",
  effect: "Эффект",
  analog: "Аналогия",
  combined: "Комбинированный",
};

const METHOD_COLORS: Record<string, string> = {
  principle: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  standard: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  effect: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  analog: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  combined: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
};

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 dark:text-gray-400 w-28">
        {label}
      </span>
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className="bg-primary-500 h-2 rounded-full transition-all"
          style={{ width: `${value * 10}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-6 text-right">
        {value}
      </span>
    </div>
  );
}

export default function SolutionCard({ solution }: SolutionCardProps) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          {solution.title}
        </h3>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ml-2 ${
            METHOD_COLORS[solution.method_used] || ""
          }`}
        >
          {METHOD_LABELS[solution.method_used] || solution.method_used}
        </span>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {solution.description}
      </p>

      <div className="space-y-2">
        <ScoreBar label="Новизна" value={solution.novelty_score} />
        <ScoreBar label="Реализуемость" value={solution.feasibility_score} />
      </div>
    </div>
  );
}
