import { useCallback, useEffect, useRef } from "react";
import { getTaskStatus } from "@/api/sessions";

interface UseStepPollingOptions {
  sessionId: number;
  taskId: string | null;
  onComplete: () => void;
  onError?: (error: unknown) => void;
  initialInterval?: number;
  maxInterval?: number;
  backoffFactor?: number;
}

/**
 * Polls a Celery task status with exponential backoff.
 * Starts at 1s, backs off to 3s max.
 */
export function useStepPolling({
  sessionId,
  taskId,
  onComplete,
  onError,
  initialInterval = 1000,
  maxInterval = 3000,
  backoffFactor = 1.5,
}: UseStepPollingOptions) {
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentDelay = useRef(initialInterval);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
    currentDelay.current = initialInterval;
  }, [initialInterval]);

  const poll = useCallback(async () => {
    if (!taskId) return;

    try {
      const status = await getTaskStatus(sessionId, taskId);

      if (status.ready) {
        stopPolling();
        onComplete();
        return;
      }

      // Schedule next poll with backoff
      currentDelay.current = Math.min(
        currentDelay.current * backoffFactor,
        maxInterval,
      );
      intervalRef.current = setTimeout(poll, currentDelay.current);
    } catch (err) {
      stopPolling();
      onError?.(err);
    }
  }, [sessionId, taskId, onComplete, onError, stopPolling, backoffFactor, maxInterval]);

  useEffect(() => {
    if (taskId) {
      currentDelay.current = initialInterval;
      intervalRef.current = setTimeout(poll, initialInterval);
    }

    return stopPolling;
  }, [taskId, poll, stopPolling, initialInterval]);

  return { stopPolling };
}
