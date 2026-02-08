import { useCallback, useEffect, useState } from "react";
import { useSessionStore } from "@/store/sessionStore";
import { useStepPolling } from "./useStepPolling";

/**
 * Hook for managing an ARIZ session — submit, advance, back, polling.
 */
export function useSession(sessionId: number) {
  const {
    session,
    progress,
    currentStep,
    isSubmitting,
    pollingTaskId,
    loadSession,
    loadProgress,
    loadCurrentStep,
    submitStep,
    advanceStep,
    goBack,
    setPollingTaskId,
  } = useSessionStore();

  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    loadSession(sessionId);
    loadProgress(sessionId);
    loadCurrentStep(sessionId);
  }, [sessionId, loadSession, loadProgress, loadCurrentStep]);

  // Polling callback
  const handlePollComplete = useCallback(async () => {
    setIsPolling(false);
    setPollingTaskId(null);
    await loadCurrentStep(sessionId);
    await loadProgress(sessionId);
  }, [sessionId, loadCurrentStep, loadProgress, setPollingTaskId]);

  const handlePollError = useCallback((err: unknown) => {
    setIsPolling(false);
    setError("Ошибка при обработке. Попробуйте ещё раз.");
    console.error("Polling error:", err);
  }, []);

  useStepPolling({
    sessionId,
    taskId: pollingTaskId,
    onComplete: handlePollComplete,
    onError: handlePollError,
  });

  const handleSubmit = useCallback(
    async (userInput: string) => {
      setError(null);
      try {
        await submitStep(sessionId, userInput);
        setIsPolling(true);
      } catch {
        setError("Не удалось отправить ответ.");
      }
    },
    [sessionId, submitStep],
  );

  const handleAdvance = useCallback(async () => {
    setError(null);
    try {
      const completed = await advanceStep(sessionId);
      if (completed) {
        await loadSession(sessionId);
      }
      await loadProgress(sessionId);
    } catch {
      setError("Не удалось перейти к следующему шагу.");
    }
  }, [sessionId, advanceStep, loadProgress, loadSession]);

  const handleBack = useCallback(async () => {
    setError(null);
    try {
      await goBack(sessionId);
      await loadProgress(sessionId);
    } catch {
      setError("Невозможно вернуться назад.");
    }
  }, [sessionId, goBack, loadProgress]);

  return {
    session,
    progress,
    currentStep,
    isSubmitting,
    isPolling,
    error,
    handleSubmit,
    handleAdvance,
    handleBack,
  };
}
