import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProblem } from "@/api/problems";
import { startSession } from "@/api/sessions";

const MODES = [
  {
    value: "express",
    label: "Экспресс",
    description: "7 шагов — быстрый анализ для простых задач",
    badge: "5-10 мин",
    color: "border-green-500 bg-green-50 dark:bg-green-900/20",
    activeRing: "ring-green-500/40",
  },
  {
    value: "full",
    label: "Полный АРИЗ-2010",
    description: "24 шага — глубокий анализ по методологии В. Петрова",
    badge: "30-60 мин",
    color: "border-purple-500 bg-purple-50 dark:bg-purple-900/20",
    activeRing: "ring-purple-500/40",
  },
  {
    value: "autopilot",
    label: "Автопилот",
    description: "ИИ проходит все шаги самостоятельно",
    badge: "1-3 мин",
    color: "border-amber-500 bg-amber-50 dark:bg-amber-900/20",
    activeRing: "ring-amber-500/40",
  },
] as const;

const DOMAINS = [
  { value: "technical", label: "Техническая" },
  { value: "business", label: "Бизнес" },
  { value: "everyday", label: "Бытовая" },
] as const;

export default function NewProblemPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [mode, setMode] = useState<string>("express");
  const [domain, setDomain] = useState<string>("technical");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const problem = await createProblem({
        title,
        original_description: description,
        mode,
        domain,
      });

      const session = await startSession(problem.id, mode);
      navigate(`/sessions/${session.id}`);
    } catch {
      setError("Не удалось создать задачу. Попробуйте ещё раз.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Новая задача
      </h1>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Название задачи
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Например: Перегрев трубы при работе компрессора"
            className="input-field"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Описание проблемы
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={5}
            placeholder="Опишите проблему подробно: что происходит, какие ограничения, что уже пробовали..."
            className="input-field resize-y"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Режим анализа
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {MODES.map((m) => (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={`p-4 rounded-lg border text-left transition-all ${
                  mode === m.value
                    ? `${m.color} ring-2 ${m.activeRing}`
                    : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900 dark:text-white text-sm">
                    {m.label}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                    {m.badge}
                  </span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {m.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Область
          </label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="input-field"
          >
            {DOMAINS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full btn-primary py-3 text-base"
        >
          {isSubmitting ? "Создаём..." : "Начать анализ"}
        </button>
      </form>
    </div>
  );
}
