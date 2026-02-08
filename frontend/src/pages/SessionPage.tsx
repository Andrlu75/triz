import { useCallback, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useSession } from "@/hooks/useSession";
import ChatInterface from "@/components/session/ChatInterface";
import StepProgress from "@/components/session/StepProgress";
import Spinner from "@/components/common/Spinner";
import Modal from "@/components/common/Modal";
import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import { MODE_LABELS } from "@/utils/constants";
import type { StepResult } from "@/api/types";

/**
 * SessionPage -- the main working page of the TRIZ Solver.
 *
 * Layout:
 * - Desktop: StepProgress sidebar (left) + ChatInterface (right)
 * - Mobile: compact StepProgress bar (top) + ChatInterface (full width)
 *
 * Features:
 * - Loads session, progress, and current step on mount
 * - Submit user input -> polls Celery task -> shows LLM response
 * - Advance / go back between steps
 * - Click completed step to review its result in a modal
 * - Navigate to summary when session is completed
 */
export default function SessionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sessionId = Number(id);

  const {
    session,
    progress,
    currentStep,
    isSubmitting,
    isPolling,
    isAdvancing,
    error,
    handleSubmit,
    handleAdvance,
    handleBack,
    clearError,
  } = useSession(sessionId);

  // Step review modal state
  const [reviewStep, setReviewStep] = useState<StepResult | null>(null);

  const handleStepClick = useCallback(
    (code: string) => {
      if (!session) return;
      const step = session.steps.find((s) => s.step_code === code);
      if (step) setReviewStep(step);
    },
    [session],
  );

  // ---------------------------------------------------------------------------
  // Loading state
  // ---------------------------------------------------------------------------
  if (!session || !progress) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Spinner size="lg" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Загрузка сессии...
        </p>
      </div>
    );
  }

  const isCompleted = session.status === "completed";
  const canAdvance =
    currentStep?.status === "completed" && !isCompleted && !isPolling;
  const canGoBack = progress.current_index > 0 && !isPolling;

  return (
    <div className="animate-fade-in">
      {/* Mobile StepProgress (visible on small screens) */}
      <div className="lg:hidden mb-4">
        <StepProgress
          progress={progress}
          onStepClick={handleStepClick}
          compact
        />
      </div>

      <div className="flex gap-6 h-[calc(100vh-10rem)] lg:h-[calc(100vh-8rem)]">
        {/* Desktop sidebar: StepProgress */}
        <aside className="hidden lg:block w-64 flex-shrink-0">
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto">
            <StepProgress
              progress={progress}
              onStepClick={handleStepClick}
            />
          </div>
        </aside>

        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Session header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                {MODE_LABELS[session.mode] || session.mode}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Шаг {progress.current_step} из {progress.total_steps}
                {progress.current_step_name && ` \u2014 ${progress.current_step_name}`}
                {isCompleted && " \u2014 Анализ завершён"}
              </p>
            </div>

            <div className="flex gap-2 flex-shrink-0">
              {canGoBack && (
                <button
                  onClick={handleBack}
                  className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  Назад
                </button>
              )}
              {canAdvance && (
                <button
                  onClick={handleAdvance}
                  disabled={isAdvancing}
                  className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5"
                >
                  {isAdvancing ? (
                    <>
                      <Spinner size="sm" />
                      Переход...
                    </>
                  ) : (
                    "Далее"
                  )}
                </button>
              )}
              {isCompleted && (
                <button
                  onClick={() => navigate(`/sessions/${sessionId}/summary`)}
                  className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors inline-flex items-center gap-1.5"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Итоги
                </button>
              )}
            </div>
          </div>

          {/* Error banner */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4 text-sm flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={clearError}
                className="text-red-500 hover:text-red-700 dark:hover:text-red-300 ml-3"
                aria-label="Закрыть"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          )}

          {/* Chat interface */}
          <div className="flex-1 min-h-0">
            <ChatInterface
              steps={session.steps}
              currentStep={currentStep}
              isPolling={isPolling}
              isSubmitting={isSubmitting}
              isCompleted={isCompleted}
              onSubmit={handleSubmit}
            />
          </div>
        </div>
      </div>

      {/* Step review modal */}
      <Modal
        open={reviewStep !== null}
        onClose={() => setReviewStep(null)}
        title={reviewStep ? `Шаг ${reviewStep.step_code}: ${reviewStep.step_name}` : ""}
        maxWidth="lg"
      >
        {reviewStep && (
          <div className="space-y-4">
            {reviewStep.user_input && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Ваш ответ
                </p>
                <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-3 text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                  {reviewStep.user_input}
                </div>
              </div>
            )}
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Результат анализа
              </p>
              <MarkdownRenderer
                content={
                  reviewStep.validated_result || reviewStep.llm_output || "Нет данных"
                }
              />
            </div>
            {reviewStep.validation_notes && (
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Заметки валидации
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {reviewStep.validation_notes}
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
