// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface User {
  id: number;
  username: string;
  email: string;
  plan: "free" | "pro" | "business";
  locale: string;
  date_joined: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

// ---------------------------------------------------------------------------
// Problems
// ---------------------------------------------------------------------------

export type ProblemMode = "express" | "full" | "autopilot";
export type ProblemDomain = "technical" | "business" | "everyday";
export type ProblemStatus = "draft" | "in_progress" | "completed" | "archived";

export interface Problem {
  id: number;
  title: string;
  original_description: string;
  mode: ProblemMode;
  domain: ProblemDomain;
  status: ProblemStatus;
  final_report: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProblemListItem {
  id: number;
  title: string;
  mode: ProblemMode;
  domain: ProblemDomain;
  status: ProblemStatus;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Sessions / Steps
// ---------------------------------------------------------------------------

export type SessionStatus = "active" | "completed" | "abandoned";

export interface StepResult {
  id: number;
  step_code: string;
  step_name: string;
  user_input: string;
  llm_output: string;
  validated_result: string;
  validation_notes: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  created_at: string;
}

export interface Contradiction {
  id: number;
  type: "surface" | "deepened" | "sharpened";
  quality_a: string;
  quality_b: string;
  property_s: string;
  anti_property_s: string;
  formulation: string;
}

export interface IKR {
  id: number;
  formulation: string;
  strengthened_formulation: string;
  vpr_used: string[];
}

export interface Solution {
  id: number;
  method_used: string;
  title: string;
  description: string;
  novelty_score: number;
  feasibility_score: number;
  created_at: string;
}

export interface Session {
  id: number;
  problem: number;
  mode: ProblemMode;
  current_step: string;
  current_part: number;
  status: SessionStatus;
  completed_at: string | null;
  created_at: string;
  steps: StepResult[];
  contradictions: Contradiction[];
  ikrs: IKR[];
  solutions: Solution[];
}

export interface SessionListItem {
  id: number;
  problem: number;
  problem_title: string;
  mode: ProblemMode;
  current_step: string;
  status: SessionStatus;
  created_at: string;
}

export interface SessionProgress {
  current_step: string;
  current_step_name: string;
  current_index: number;
  total_steps: number;
  completed_count: number;
  percent: number;
  steps_completed: Array<{
    code: string;
    name: string;
    completed: boolean;
  }>;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  ready: boolean;
  result?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Paginated response
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
