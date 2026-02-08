import { useCallback, useEffect, useRef, useState } from "react";
import { getTaskStatus } from "@/api/sessions";
import type { TaskStatus } from "@/api/types";
import { POLLING } from "@/utils/constants";

interface UseStepPollingOptions {
  sessionId: number;
  taskId: string | null;
  onComplete?: (status: TaskStatus) => void;
  onError?: (error: string) => void;
}

interface UseStepPollingReturn {
  isPolling: boolean;
  result: TaskStatus | null;
  error: string | null;
  stopPolling: () => void;
}

/**
 * Polls a Celery task status with exponential backoff.
 *
 * Backoff schedule: 1s -> 1.5s -> 2.25s -> 3s (capped).
 * Stops polling when task is ready or when an error occurs.
 * Returns `{ isPolling, result, error, stopPolling }`.
 */
export function useStepPolling({
  sessionId,
  taskId,
  onComplete,
  onError,
}: UseStepPollingOptions): UseStepPollingReturn {
  const [isPolling, setIsPolling] = useState(false);
  const [result, setResult] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const delayRef = useRef<number>(POLLING.INITIAL_INTERVAL_MS);
  const retriesRef = useRef<number>(0);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Keep callback refs up to date without re-triggering effects
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    clearTimer();
    setIsPolling(false);
    delayRef.current = POLLING.INITIAL_INTERVAL_MS;
    retriesRef.current = 0;
  }, [clearTimer]);

  const poll = useCallback(async () => {
    if (!taskId || !sessionId) return;

    try {
      const status = await getTaskStatus(sessionId, taskId);

      if (status.ready) {
        setResult(status);
        setIsPolling(false);
        delayRef.current = POLLING.INITIAL_INTERVAL_MS;
        retriesRef.current = 0;
        onCompleteRef.current?.(status);
        return;
      }

      if (status.status === "FAILURE") {
        const msg = "Ошибка обработки. Попробуйте отправить ещё раз.";
        setError(msg);
        setIsPolling(false);
        delayRef.current = POLLING.INITIAL_INTERVAL_MS;
        retriesRef.current = 0;
        onErrorRef.current?.(msg);
        return;
      }

      // Check max retries
      retriesRef.current += 1;
      if (retriesRef.current >= POLLING.MAX_RETRIES) {
        const msg = "Превышено время ожидания ответа.";
        setError(msg);
        setIsPolling(false);
        delayRef.current = POLLING.INITIAL_INTERVAL_MS;
        retriesRef.current = 0;
        onErrorRef.current?.(msg);
        return;
      }

      // Schedule next poll with backoff
      delayRef.current = Math.min(
        delayRef.current * POLLING.BACKOFF_FACTOR,
        POLLING.MAX_INTERVAL_MS,
      );
      timerRef.current = setTimeout(poll, delayRef.current);
    } catch {
      const msg = "Не удалось проверить статус задачи.";
      setError(msg);
      setIsPolling(false);
      delayRef.current = POLLING.INITIAL_INTERVAL_MS;
      retriesRef.current = 0;
      onErrorRef.current?.(msg);
    }
  }, [sessionId, taskId]);

  // Start / stop polling when taskId changes
  useEffect(() => {
    if (!taskId) {
      return;
    }

    setIsPolling(true);
    setResult(null);
    setError(null);
    delayRef.current = POLLING.INITIAL_INTERVAL_MS;
    retriesRef.current = 0;

    // First poll after initial interval
    timerRef.current = setTimeout(poll, POLLING.INITIAL_INTERVAL_MS);

    return () => {
      clearTimer();
    };
  }, [taskId, poll, clearTimer]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  return { isPolling, result, error, stopPolling };
}
