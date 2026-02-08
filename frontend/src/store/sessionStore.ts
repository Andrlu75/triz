import { create } from "zustand";
import type { Session, SessionProgress, StepResult } from "@/api/types";
import * as sessionsApi from "@/api/sessions";

interface SessionState {
  session: Session | null;
  progress: SessionProgress | null;
  currentStep: StepResult | null;
  isSubmitting: boolean;
  pollingTaskId: string | null;

  loadSession: (id: number) => Promise<void>;
  loadProgress: (id: number) => Promise<void>;
  loadCurrentStep: (id: number) => Promise<void>;
  submitStep: (sessionId: number, userInput: string) => Promise<string>;
  advanceStep: (sessionId: number) => Promise<boolean>;
  goBack: (sessionId: number) => Promise<void>;
  setPollingTaskId: (taskId: string | null) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  progress: null,
  currentStep: null,
  isSubmitting: false,
  pollingTaskId: null,

  loadSession: async (id) => {
    const session = await sessionsApi.getSession(id);
    set({ session });
  },

  loadProgress: async (id) => {
    const progress = await sessionsApi.getProgress(id);
    set({ progress });
  },

  loadCurrentStep: async (id) => {
    const step = await sessionsApi.getCurrentStep(id);
    set({ currentStep: step });
  },

  submitStep: async (sessionId, userInput) => {
    set({ isSubmitting: true });
    try {
      const { task_id } = await sessionsApi.submitStep(sessionId, userInput);
      set({ pollingTaskId: task_id });
      return task_id;
    } finally {
      set({ isSubmitting: false });
    }
  },

  advanceStep: async (sessionId) => {
    const result = await sessionsApi.advanceStep(sessionId);
    if ("completed" in result && result.completed) {
      return true; // session completed
    }
    set({ currentStep: result as StepResult });
    return false;
  },

  goBack: async (sessionId) => {
    const step = await sessionsApi.goBack(sessionId);
    set({ currentStep: step });
  },

  setPollingTaskId: (taskId) => set({ pollingTaskId: taskId }),

  reset: () =>
    set({
      session: null,
      progress: null,
      currentStep: null,
      isSubmitting: false,
      pollingTaskId: null,
    }),
}));
