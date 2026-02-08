import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

const FEATURES = [
  {
    title: "Экспресс-режим",
    description:
      "7 шагов для быстрого анализа. Идеально для новичков и простых задач. ИИ ведёт диалог на бытовом языке.",
    steps: "7 шагов",
    time: "5-10 мин",
    color: "text-green-500 dark:text-green-400",
    border: "border-green-500/20",
  },
  {
    title: "Полный АРИЗ-2010",
    description:
      "24 шага по В. Петрову. Глубокий анализ для сложных инженерных задач. 28 правил валидации.",
    steps: "24 шага",
    time: "30-60 мин",
    color: "text-purple-500 dark:text-purple-400",
    border: "border-purple-500/20",
  },
  {
    title: "Автопилот",
    description:
      "ИИ проходит все шаги самостоятельно и предлагает готовые решения со структурированным отчётом.",
    steps: "Автоматически",
    time: "1-3 мин",
    color: "text-amber-500 dark:text-amber-400",
    border: "border-amber-500/20",
  },
] as const;

const STEPS = [
  "Формулировка задачи",
  "Поверхностное противоречие (ПП)",
  "Углублённое противоречие (УП)",
  "Идеальный конечный результат (ИКР)",
  "Обострённое противоречие (ОП)",
  "Углубление ОП",
  "Решение",
] as const;

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="min-h-[60vh] flex items-center justify-center py-16">
        <div className="text-center max-w-3xl">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            ТРИЗ-Решатель
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-4">
            AI-платформа для решения изобретательских задач по методологии
            АРИЗ-2010
          </p>
          <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-xl mx-auto">
            Пошаговый диалог с ИИ-экспертом ТРИЗ. Формулируйте задачу, выявляйте
            противоречия, находите идеальные решения.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <>
                <Link
                  to="/problems/new"
                  className="bg-primary-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  Начать решение
                </Link>
                <Link to="/dashboard" className="btn-secondary px-6 py-3 text-lg">
                  Мои задачи
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="bg-primary-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  Начать бесплатно
                </Link>
                <Link to="/login" className="btn-secondary px-6 py-3 text-lg">
                  Войти
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Modes */}
      <section className="py-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-8">
          Три режима анализа
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className={`card p-6 ${f.border} hover:shadow-md transition-shadow`}
            >
              <h3 className={`font-semibold text-lg mb-2 ${f.color}`}>
                {f.title}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
                {f.description}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
                <span>{f.steps}</span>
                <span>{f.time}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ARIZ Steps */}
      <section className="py-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-2">
          Как это работает
        </h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-8">
          Цепочка АРИЗ: от задачи к решению
        </p>
        <div className="max-w-lg mx-auto space-y-3">
          {STEPS.map((step, i) => (
            <div key={step} className="flex items-center gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600/10 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400 flex items-center justify-center text-sm font-bold">
                {i + 1}
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {step}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
