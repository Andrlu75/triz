import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ProblemListItem } from "@/api/types";
import { listProblems } from "@/api/problems";
import {
  MODE_LABELS,
  STATUS_LABELS,
  STATUS_COLORS,
  DOMAIN_LABELS,
} from "@/utils/constants";
import { formatTimeAgo } from "@/utils/formatters";

export default function DashboardPage() {
  const [problems, setProblems] = useState<ProblemListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listProblems()
      .then((data) => setProblems(data.results))
      .catch(() => setError("Не удалось загрузить задачи."))
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
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Мои задачи
        </h1>
        <Link to="/problems/new" className="btn-primary">
          Новая задача
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      {problems.length === 0 ? (
        <div className="card text-center py-16 px-6">
          <svg
            className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
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
              className="card block p-4 hover:border-primary-300 dark:hover:border-primary-600 transition-colors animate-slide-up"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-medium text-gray-900 dark:text-white">
                    {p.title}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {MODE_LABELS[p.mode] || p.mode}
                    {" \u00b7 "}
                    {DOMAIN_LABELS[p.domain] || p.domain}
                    {" \u00b7 "}
                    {formatTimeAgo(p.created_at)}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${STATUS_COLORS[p.status] || ""}`}
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
