import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="text-center max-w-2xl">
        <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6">
          ТРИЗ-Решатель
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-4">
          AI-платформа для решения изобретательских задач по методологии
          АРИЗ-2010
        </p>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Пошаговый диалог с ИИ-экспертом ТРИЗ. Формулируйте задачу,
          выявляйте противоречия, находите идеальные решения.
        </p>

        <div className="flex gap-4 justify-center">
          {isAuthenticated ? (
            <>
              <Link
                to="/problems/new"
                className="bg-primary-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary-700"
              >
                Начать решение
              </Link>
              <Link
                to="/dashboard"
                className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-6 py-3 rounded-lg text-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Мои задачи
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/register"
                className="bg-primary-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary-700"
              >
                Начать бесплатно
              </Link>
              <Link
                to="/login"
                className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-6 py-3 rounded-lg text-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Войти
              </Link>
            </>
          )}
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-2">
              Экспресс-режим
            </h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              7 шагов для быстрого анализа. Идеально для новичков и простых задач.
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-2">
              Полный АРИЗ-2010
            </h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              24 шага по В. Петрову. Глубокий анализ для сложных инженерных задач.
            </p>
          </div>
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-2">
              Автопилот
            </h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              ИИ проходит все шаги самостоятельно и предлагает готовые решения.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
