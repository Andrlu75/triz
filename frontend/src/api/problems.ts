import api from "./client";
import type { PaginatedResponse, Problem, ProblemListItem } from "./types";

export async function listProblems(): Promise<PaginatedResponse<ProblemListItem>> {
  const { data } = await api.get<PaginatedResponse<ProblemListItem>>("/problems/");
  return data;
}

export async function getProblem(id: number): Promise<Problem> {
  const { data } = await api.get<Problem>(`/problems/${id}/`);
  return data;
}

export async function createProblem(payload: {
  title: string;
  original_description: string;
  mode?: string;
  domain?: string;
}): Promise<Problem> {
  const { data } = await api.post<Problem>("/problems/", payload);
  return data;
}

export async function updateProblem(
  id: number,
  payload: Partial<Pick<Problem, "title" | "original_description" | "mode" | "domain">>,
): Promise<Problem> {
  const { data } = await api.patch<Problem>(`/problems/${id}/`, payload);
  return data;
}

export async function deleteProblem(id: number): Promise<void> {
  await api.delete(`/problems/${id}/`);
}
