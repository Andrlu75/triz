import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StepProgress from "@/components/session/StepProgress";
import type { SessionProgress } from "@/api/types";

const mockProgress: SessionProgress = {
  current_step: "2",
  current_step_name: "Поверхностное противоречие",
  current_index: 1,
  total_steps: 7,
  completed_count: 1,
  percent: 14,
  steps_completed: [
    { code: "1", name: "Формулировка задачи", completed: true },
    { code: "2", name: "Поверхностное противоречие", completed: false },
    { code: "3", name: "Углублённое противоречие", completed: false },
    { code: "4", name: "ИКР", completed: false },
    { code: "5", name: "Обострённое противоречие", completed: false },
    { code: "6", name: "Углубление ОП", completed: false },
    { code: "7", name: "Решение", completed: false },
  ],
};

describe("StepProgress", () => {
  it("renders all steps", () => {
    render(<StepProgress progress={mockProgress} />);
    expect(screen.getByText("Формулировка задачи")).toBeDefined();
    expect(screen.getByText("Поверхностное противоречие")).toBeDefined();
    expect(screen.getByText("Решение")).toBeDefined();
  });

  it("shows progress count", () => {
    render(<StepProgress progress={mockProgress} />);
    expect(screen.getByText("1/7 (14%)")).toBeDefined();
  });

  it("calls onStepClick for completed steps", () => {
    const onClick = vi.fn();
    render(<StepProgress progress={mockProgress} onStepClick={onClick} />);

    const completedButton = screen.getByText("Формулировка задачи").closest("button")!;
    fireEvent.click(completedButton);
    expect(onClick).toHaveBeenCalledWith("1");
  });

  it("does not call onStepClick for incomplete steps", () => {
    const onClick = vi.fn();
    render(<StepProgress progress={mockProgress} onStepClick={onClick} />);

    const incompleteButton = screen.getByText("Решение").closest("button")!;
    fireEvent.click(incompleteButton);
    expect(onClick).not.toHaveBeenCalled();
  });
});
