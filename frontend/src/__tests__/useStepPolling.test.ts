import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

// Mock the API module
vi.mock("@/api/sessions", () => ({
  getTaskStatus: vi.fn(),
}));

// Mock constants
vi.mock("@/utils/constants", () => ({
  POLLING: {
    INITIAL_INTERVAL_MS: 100,
    MAX_INTERVAL_MS: 300,
    BACKOFF_FACTOR: 1.5,
    MAX_RETRIES: 5,
  },
}));

import { renderHook, act, waitFor } from "@testing-library/react";
import { useStepPolling } from "@/hooks/useStepPolling";
import { getTaskStatus } from "@/api/sessions";

const mockGetTaskStatus = getTaskStatus as ReturnType<typeof vi.fn>;

describe("useStepPolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockGetTaskStatus.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not poll when taskId is null", () => {
    renderHook(() =>
      useStepPolling({
        sessionId: 1,
        taskId: null,
      }),
    );

    vi.advanceTimersByTime(5000);
    expect(mockGetTaskStatus).not.toHaveBeenCalled();
  });

  it("starts polling when taskId is provided", async () => {
    mockGetTaskStatus.mockResolvedValue({
      task_id: "abc",
      status: "PENDING",
      ready: false,
    });

    renderHook(() =>
      useStepPolling({
        sessionId: 1,
        taskId: "abc",
      }),
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    expect(mockGetTaskStatus).toHaveBeenCalledWith(1, "abc");
  });

  it("calls onComplete when task is ready", async () => {
    const onComplete = vi.fn();

    mockGetTaskStatus.mockResolvedValue({
      task_id: "abc",
      status: "SUCCESS",
      ready: true,
      result: { step_code: "1" },
    });

    renderHook(() =>
      useStepPolling({
        sessionId: 1,
        taskId: "abc",
        onComplete,
      }),
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it("stops polling when stopPolling is called", async () => {
    mockGetTaskStatus.mockResolvedValue({
      task_id: "abc",
      status: "PENDING",
      ready: false,
    });

    const { result } = renderHook(() =>
      useStepPolling({
        sessionId: 1,
        taskId: "abc",
      }),
    );

    act(() => {
      result.current.stopPolling();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    // Should only poll once before being stopped
    expect(mockGetTaskStatus.mock.calls.length).toBeLessThanOrEqual(1);
  });
});
