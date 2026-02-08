import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatInterface from "@/components/session/ChatInterface";
import type { StepResult } from "@/api/types";

const completedStep: StepResult = {
  id: 1,
  step_code: "1",
  step_name: "Формулировка задачи",
  user_input: "Труба перегревается",
  llm_output: "Анализ задачи показал...",
  validated_result: "",
  validation_notes: "",
  status: "completed",
  created_at: "2026-01-01T00:00:00Z",
};

const pendingStep: StepResult = {
  id: 2,
  step_code: "2",
  step_name: "Поверхностное противоречие",
  user_input: "",
  llm_output: "",
  validated_result: "",
  validation_notes: "",
  status: "pending",
  created_at: "2026-01-01T00:01:00Z",
};

describe("ChatInterface", () => {
  it("renders completed steps with user input and LLM response", () => {
    render(
      <ChatInterface
        steps={[completedStep]}
        currentStep={pendingStep}
        isPolling={false}
        isSubmitting={false}
        isCompleted={false}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText("Труба перегревается")).toBeDefined();
    expect(screen.getByText("Анализ задачи показал...")).toBeDefined();
  });

  it("shows ThinkingIndicator when polling", () => {
    render(
      <ChatInterface
        steps={[completedStep]}
        currentStep={pendingStep}
        isPolling={true}
        isSubmitting={false}
        isCompleted={false}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText("ТРИЗ-эксперт анализирует...")).toBeDefined();
  });

  it("disables input when polling", () => {
    render(
      <ChatInterface
        steps={[]}
        currentStep={pendingStep}
        isPolling={true}
        isSubmitting={false}
        isCompleted={false}
        onSubmit={vi.fn()}
      />,
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveProperty("disabled", true);
  });

  it("calls onSubmit with text when submitted", () => {
    const onSubmit = vi.fn();
    render(
      <ChatInterface
        steps={[]}
        currentStep={pendingStep}
        isPolling={false}
        isSubmitting={false}
        isCompleted={false}
        onSubmit={onSubmit}
      />,
    );

    const textarea = screen.getByRole("textbox");
    const submitButton = screen.getByLabelText("Отправить");

    fireEvent.change(textarea, { target: { value: "My input" } });
    fireEvent.click(submitButton);

    expect(onSubmit).toHaveBeenCalledWith("My input");
  });

  it("hides input area when session is completed", () => {
    render(
      <ChatInterface
        steps={[completedStep]}
        currentStep={null}
        isPolling={false}
        isSubmitting={false}
        isCompleted={true}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getByText("Анализ завершён")).toBeDefined();
  });

  it("shows welcome message when no completed steps yet", () => {
    render(
      <ChatInterface
        steps={[]}
        currentStep={pendingStep}
        isPolling={false}
        isSubmitting={false}
        isCompleted={false}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText("ТРИЗ-эксперт готов к работе")).toBeDefined();
  });
});
