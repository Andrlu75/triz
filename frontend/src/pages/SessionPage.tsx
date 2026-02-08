import { useParams, useNavigate } from "react-router-dom";
import { useSession } from "@/hooks/useSession";
import ChatInterface from "@/components/session/ChatInterface";
import StepProgress from "@/components/session/StepProgress";
import Spinner from "@/components/common/Spinner";

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
    error,
    handleSubmit,
    handleAdvance,
    handleBack,
  } = useSession(sessionId);

  if (!session || !progress) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  const isCompleted = session.status === "completed";
  const canAdvance =
    currentStep?.status === "completed" && !isCompleted;
  const canGoBack = progress.current_index > 0;

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)]">
      {/* Sidebar — Step Progress */}
      <aside className="hidden lg:block w-64 flex-shrink-0">
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 sticky top-24">
          <StepProgress progress={progress} />
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {session.mode === "express"
                ? "Экспресс-АРИЗ"
                : session.mode === "full"
                  ? "Полный АРИЗ-2010"
                  : "Автопилот"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Шаг {progress.current_step} из {progress.total_steps}
              {isCompleted && " — Анализ завершён"}
            </p>
          </div>

          <div className="flex gap-2">
            {canGoBack && (
              <button
                onClick={handleBack}
                className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Назад
              </button>
            )}
            {canAdvance && (
              <button
                onClick={handleAdvance}
                className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Далее
              </button>
            )}
            {isCompleted && (
              <button
                onClick={() => navigate(`/sessions/${sessionId}/summary`)}
                className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Итоги
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Chat */}
        <div className="flex-1 min-h-0">
          <ChatInterface
            steps={session.steps}
            currentStep={currentStep}
            isPolling={isPolling}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmit}
          />
        </div>
      </div>
    </div>
  );
}
