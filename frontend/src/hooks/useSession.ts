import { useCallback, useEffect, useState } from "react";
import { useSessionStore } from "@/store/sessionStore";
import { useStepPolling } from "./useStepPolling";
import type { TaskStatus } from "@/api/types";

/**
 * High-level hook for managing an ARIZ session.
 *
 * Handles submit, advance, back, and Celery task polling with backoff.
 * Returns everything the SessionPage needs to render the chat UI.
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
  const [isAdvancing, setIsAdvancing] = useState(false);

  // ---------------------------------------------------------------------------
  // Initial load
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!sessionId || isNaN(sessionId)) return;

    loadSession(sessionId);
    loadProgress(sessionId);
    loadCurrentStep(sessionId);
  }, [sessionId, loadSession, loadProgress, loadCurrentStep]);

  // ---------------------------------------------------------------------------
  // Polling callbacks
  // ---------------------------------------------------------------------------
  const handlePollComplete = useCallback(
    async (_status: TaskStatus) => {
      setIsPolling(false);
      setPollingTaskId(null);
      await loadCurrentStep(sessionId);
      await loadProgress(sessionId);
      await loadSession(sessionId);
    },
    [sessionId, loadCurrentStep, loadProgress, loadSession, setPollingTaskId],
  );

  const handlePollError = useCallback(
    (msg: string) => {
      setIsPolling(false);
      setPollingTaskId(null);
      setError(msg);
    },
    [setPollingTaskId],
  );

  const { isPolling: polling } = useStepPolling({
    sessionId,
    taskId: pollingTaskId,
    onComplete: handlePollComplete,
    onError: handlePollError,
  });

  // Sync local isPolling with hook polling state
  useEffect(() => {
    if (polling) setIsPolling(true);
  }, [polling]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  /** Submit user input for the current step and start polling. */
  const handleSubmit = useCallback(
    async (userInput: string) => {
      setError(null);
      try {
        await submitStep(sessionId, userInput);
        setIsPolling(true);
      } catch {
        setError("Не удалось отправить ответ. Попробуйте ещё раз.");
      }
    },
    [sessionId, submitStep],
  );

  /** Advance to the next ARIZ step after completing the current one. */
  const handleAdvance = useCallback(async () => {
    setError(null);
    setIsAdvancing(true);
    try {
      const completed = await advanceStep(sessionId);
      if (completed) {
        await loadSession(sessionId);
      }
      await loadProgress(sessionId);
      await loadCurrentStep(sessionId);
    } catch {
      setError("Не удалось перейти к следующему шагу.");
    } finally {
      setIsAdvancing(false);
    }
  }, [sessionId, advanceStep, loadProgress, loadSession, loadCurrentStep]);

  /** Go back to the previous step. */
  const handleBack = useCallback(async () => {
    setError(null);
    try {
      await goBack(sessionId);
      await loadProgress(sessionId);
    } catch {
      setError("Невозможно вернуться назад.");
    }
  }, [sessionId, goBack, loadProgress]);

  /** Clear the current error message. */
  const clearError = useCallback(() => setError(null), []);

  return {
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
  };
}
