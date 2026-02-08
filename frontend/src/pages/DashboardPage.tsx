import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ProblemListItem } from "@/api/types";
import { listProblems } from "@/api/problems";

const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  in_progress: "В работе",
  completed: "Завершена",
  archived: "Архив",
};

const MODE_LABELS: Record<string, string> = {
  express: "Экспресс",
  full: "Полный АРИЗ",
  autopilot: "Автопилот",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  in_progress: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  archived: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
};

export default function DashboardPage() {
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listProblems()
      .then((data) => setProblems(data.results))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin h-8 w-8 border-2 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Мои задачи
        </h1>
        <Link
          to="/problems/new"
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Новая задача
        </Link>
      </div>

      {problems.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            У вас пока нет задач
          </p>
          <Link
            to="/problems/new"
            className="text-primary-600 hover:underline font-medium"
          >
            Создать первую задачу
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {problems.map((p) => (
            <Link
              key={p.id}
              to={`/problems/${p.id}`}
              className="block bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:border-primary-300 dark:hover:border-primary-600 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-medium text-gray-900 dark:text-white">
                    {p.title}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {MODE_LABELS[p.mode] || p.mode} &middot;{" "}
                    {new Date(p.created_at).toLocaleDateString("ru")}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[p.status] || ""}`}
                >
                  {STATUS_LABELS[p.status] || p.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
