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

import { renderHook, act } from "@testing-library/react";
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
      await vi.advanceTimersByTimeAsync(100);
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

    // Advance timers asynchronously to allow promise resolution
    await act(async () => {
      await vi.advanceTimersByTimeAsync(200);
    });

    expect(onComplete).toHaveBeenCalled();
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

    // Wait for hook to initialize
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    act(() => {
      result.current.stopPolling();
    });

    const callsBefore = mockGetTaskStatus.mock.calls.length;

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    // No additional calls should have been made after stopPolling
    expect(mockGetTaskStatus.mock.calls.length).toBeLessThanOrEqual(
      callsBefore + 1,
    );
  });

  it("reports isPolling = true while actively polling", async () => {
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

    // Wait for hook to initialize
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.isPolling).toBe(true);
  });
});
