import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import SolutionCard from "@/components/solutions/SolutionCard";
import type { Solution } from "@/api/types";

const baseSolution: Solution = {
  id: 1,
  method_used: "principle",
  title: "Segmentation of the pipe",
  description: "Split the overheating pipe into segments with cooling gaps between them.",
  novelty_score: 8,
  feasibility_score: 6,
  created_at: "2026-01-15T12:00:00Z",
};

describe("SolutionCard", () => {
  it("renders the solution title", () => {
    render(<SolutionCard solution={baseSolution} />);
    expect(screen.getByText("Segmentation of the pipe")).toBeDefined();
  });

  it("renders the solution description", () => {
    render(<SolutionCard solution={baseSolution} />);
    expect(
      screen.getByText(
        "Split the overheating pipe into segments with cooling gaps between them.",
      ),
    ).toBeDefined();
  });

  it("displays method label badge", () => {
    render(<SolutionCard solution={baseSolution} />);
    expect(screen.getByText("Приём")).toBeDefined();
  });

  it("shows novelty and feasibility scores", () => {
    render(<SolutionCard solution={baseSolution} />);
    expect(screen.getByText("Новизна")).toBeDefined();
    expect(screen.getByText("Реализуемость")).toBeDefined();
    expect(screen.getByText("8")).toBeDefined();
    expect(screen.getByText("6")).toBeDefined();
  });

  it("renders correct label for standard method", () => {
    const stdSolution: Solution = {
      ...baseSolution,
      id: 2,
      method_used: "standard",
    };
    render(<SolutionCard solution={stdSolution} />);
    expect(screen.getByText("Стандарт")).toBeDefined();
  });

  it("renders correct label for effect method", () => {
    const effectSolution: Solution = {
      ...baseSolution,
      id: 3,
      method_used: "effect",
    };
    render(<SolutionCard solution={effectSolution} />);
    expect(screen.getByText("Эффект")).toBeDefined();
  });

  it("renders correct label for analog method", () => {
    const analogSolution: Solution = {
      ...baseSolution,
      id: 4,
      method_used: "analog",
    };
    render(<SolutionCard solution={analogSolution} />);
    expect(screen.getByText("Аналогия")).toBeDefined();
  });

  it("renders correct label for combined method", () => {
    const combinedSolution: Solution = {
      ...baseSolution,
      id: 5,
      method_used: "combined",
    };
    render(<SolutionCard solution={combinedSolution} />);
    expect(screen.getByText("Комбинированный")).toBeDefined();
  });

  it("falls back to raw method_used for unknown methods", () => {
    const unknownSolution: Solution = {
      ...baseSolution,
      id: 6,
      method_used: "custom_method",
    };
    render(<SolutionCard solution={unknownSolution} />);
    expect(screen.getByText("custom_method")).toBeDefined();
  });

  it("renders score bars with correct width percentages", () => {
    const { container } = render(<SolutionCard solution={baseSolution} />);
    const bars = container.querySelectorAll("[style]");
    const noveltyBar = Array.from(bars).find(
      (el) => (el as HTMLElement).style.width === "80%",
    );
    const feasibilityBar = Array.from(bars).find(
      (el) => (el as HTMLElement).style.width === "60%",
    );
    expect(noveltyBar).toBeDefined();
    expect(feasibilityBar).toBeDefined();
  });
});
