import api from "./client";
import type {
  Session,
  SessionListItem,
  SessionProgress,
  StepResult,
  TaskStatus,
} from "./types";

export async function listSessions(): Promise<SessionListItem[]> {
  const { data } = await api.get<SessionListItem[]>("/sessions/");
  return data;
}

export async function getSession(id: number): Promise<Session> {
  const { data } = await api.get<Session>(`/sessions/${id}/`);
  return data;
}

export async function startSession(
  problemId: number,
  mode: string = "express",
): Promise<Session> {
  const { data } = await api.post<Session>("/sessions/start/", {
    problem_id: problemId,
    mode,
  });
  return data;
}

export async function submitStep(
  sessionId: number,
  userInput: string,
): Promise<{ task_id: string }> {
  const { data } = await api.post<{ task_id: string }>(
    `/sessions/${sessionId}/submit/`,
    { user_input: userInput },
  );
  return data;
}

export async function getTaskStatus(
  sessionId: number,
  taskId: string,
): Promise<TaskStatus> {
  const { data } = await api.get<TaskStatus>(
    `/sessions/${sessionId}/task/${taskId}/`,
  );
  return data;
}

export async function getCurrentStep(sessionId: number): Promise<StepResult> {
  const { data } = await api.get<StepResult>(
    `/sessions/${sessionId}/current-step/`,
  );
  return data;
}

export async function advanceStep(sessionId: number): Promise<StepResult | { detail: string; completed: boolean }> {
  const { data } = await api.post(`/sessions/${sessionId}/advance/`);
  return data;
}

export async function goBack(sessionId: number): Promise<StepResult> {
  const { data } = await api.post<StepResult>(`/sessions/${sessionId}/back/`);
  return data;
}

export async function getProgress(sessionId: number): Promise<SessionProgress> {
  const { data } = await api.get<SessionProgress>(
    `/sessions/${sessionId}/progress/`,
  );
  return data;
}

export async function getSummary(sessionId: number): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/sessions/${sessionId}/summary/`);
  return data;
}
