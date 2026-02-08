import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getSummary } from "@/api/sessions";
import SolutionList from "@/components/solutions/SolutionList";
import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import Spinner from "@/components/common/Spinner";
import api from "@/api/client";
import type { Solution } from "@/api/types";

type ReportFormat = "pdf" | "docx";

interface SummaryData {
  session_id: number;
  mode: string;
  status: string;
  problem: { id: number; title: string; description: string; domain: string };
  steps: Array<{
    code: string;
    name: string;
    status: string;
    user_input: string;
    result: string;
  }>;
  contradictions: Array<{ type: string; formulation: string }>;
  ikrs: Array<{ formulation: string }>;
  solutions: Solution[];
}

export default function SummaryPage() {
  const { id, sessionId: legacyId } = useParams<{ id?: string; sessionId?: string }>();
  const resolvedId = id || legacyId;
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [downloading, setDownloading] = useState<ReportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!resolvedId) return;
    getSummary(Number(resolvedId))
      .then((data) => setSummary(data as unknown as SummaryData))
      .catch(() => setError("Не удалось загрузить сводку."))
      .finally(() => setIsLoading(false));
  }, [resolvedId]);

  const handleDownload = async (format: ReportFormat) => {
    if (!resolvedId) return;
    setDownloading(format);
    try {
      const response = await api.get(
        `/reports/${resolvedId}/download/${format}/`,
        { responseType: "blob" },
      );
      const contentDisposition = response.headers["content-disposition"];
      let filename = `TRIZ_Report.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+?)"?$/);
        if (match) filename = match[1];
      }
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setError(`Не удалось скачать ${format.toUpperCase()}.`);
    } finally {
      setDownloading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
        {error}
      </div>
    );
  }

  if (!summary) return null;

  const completedSteps = summary.steps.filter((s) => s.status === "completed");

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Итоги анализа
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {summary.problem.title}
        </p>
      </div>

      {/* Steps */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Шаги анализа ({completedSteps.length})
        </h2>
        <div className="space-y-4">
          {completedSteps.map((step) => (
            <div
              key={step.code}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center text-xs">
                  {step.code}
                </span>
                <h3 className="font-medium text-gray-900 dark:text-white text-sm">
                  {step.name}
                </h3>
              </div>
              {step.result && (
                <MarkdownRenderer content={step.result} className="text-sm" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Contradictions */}
      {summary.contradictions.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Противоречия
          </h2>
          <div className="space-y-3">
            {summary.contradictions.map((c, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4"
              >
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  {c.type}
                </span>
                <p className="text-sm text-gray-900 dark:text-white mt-1">
                  {c.formulation}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* IKRs */}
      {summary.ikrs.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            ИКР
          </h2>
          {summary.ikrs.map((ikr, i) => (
            <div
              key={i}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4"
            >
              <p className="text-sm text-gray-900 dark:text-white">
                {ikr.formulation}
              </p>
            </div>
          ))}
        </section>
      )}

      {/* Solutions */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Решения
        </h2>
        <SolutionList solutions={summary.solutions} />
      </section>

      {/* Download reports */}
      <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Скачать отчёт
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Экспорт полного анализа АРИЗ в формате отчёта.
        </p>
        {error && (
          <div className="bg-red-50 text-red-700 px-3 py-2 rounded text-sm mb-3">
            {error}
          </div>
        )}
        <div className="flex gap-3">
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
          >
            {downloading === "pdf" ? "Генерируем..." : "PDF"}
          </button>
          <button
            onClick={() => handleDownload("docx")}
            disabled={downloading !== null}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {downloading === "docx" ? "Генерируем..." : "DOCX"}
          </button>
        </div>
      </section>
    </div>
  );
}
