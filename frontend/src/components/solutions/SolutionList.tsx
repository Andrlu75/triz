import { useState } from "react";
import type { Solution } from "@/api/types";
import SolutionCard from "./SolutionCard";

interface SolutionListProps {
  solutions: Solution[];
}

type SortKey = "novelty" | "feasibility";

export default function SolutionList({ solutions }: SolutionListProps) {
  const [sortBy, setSortBy] = useState<SortKey>("novelty");

  const sorted = [...solutions].sort((a, b) => {
    if (sortBy === "novelty") return b.novelty_score - a.novelty_score;
    return b.feasibility_score - a.feasibility_score;
  });

  if (solutions.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Решения пока не найдены.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Сортировка:
        </span>
        <button
          onClick={() => setSortBy("novelty")}
          className={`px-3 py-1 rounded-lg text-xs font-medium ${
            sortBy === "novelty"
              ? "bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400"
              : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          }`}
        >
          По новизне
        </button>
        <button
          onClick={() => setSortBy("feasibility")}
          className={`px-3 py-1 rounded-lg text-xs font-medium ${
            sortBy === "feasibility"
              ? "bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400"
              : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          }`}
        >
          По реализуемости
        </button>
      </div>

      <div className="space-y-4">
        {sorted.map((solution) => (
          <SolutionCard key={solution.id} solution={solution} />
        ))}
      </div>
    </div>
  );
}
