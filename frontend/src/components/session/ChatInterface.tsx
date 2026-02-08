import { useEffect, useRef } from "react";
import type { StepResult } from "@/api/types";
import LLMResponse from "./LLMResponse";
import ThinkingIndicator from "./ThinkingIndicator";
import UserInput from "./UserInput";

interface ChatInterfaceProps {
  steps: StepResult[];
  currentStep: StepResult | null;
  isPolling: boolean;
  isSubmitting: boolean;
  isCompleted: boolean;
  onSubmit: (text: string) => void;
}

/**
 * Chat-style interface for an ARIZ session.
 *
 * Displays the dialogue between the user and the LLM:
 * - Completed steps shown as LLM response cards + user messages
 * - Current step input / thinking indicator
 * - Auto-scrolls to the latest content
 */
export default function ChatInterface({
  steps,
  currentStep,
  isPolling,
  isSubmitting,
  isCompleted,
  onSubmit,
}: ChatInterfaceProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom whenever content changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps, currentStep, isPolling]);

  const completedSteps = steps.filter(
    (s) => s.status === "completed" && s.llm_output,
  );

  const isWaiting = isPolling || isSubmitting;
  const canInput =
    !isCompleted && currentStep?.status === "pending" && !isWaiting;

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pb-4 scroll-smooth"
      >
        {/* Welcome message if no steps yet */}
        {completedSteps.length === 0 && !isPolling && currentStep?.status === "pending" && (
          <div className="bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl border border-primary-200 dark:border-primary-800 p-5">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center flex-shrink-0">
                <svg
                  className="h-4 w-4 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5.002 5.002 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white text-sm">
                  ТРИЗ-эксперт готов к работе
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Опишите вашу проблемную ситуацию, и мы пройдём через шаги АРИЗ
                  для поиска изобретательского решения.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Completed steps: user input + LLM response pairs */}
        {completedSteps.map((step) => (
          <div key={step.id} className="space-y-3">
            {/* User message bubble */}
            {step.user_input && (
              <div className="flex justify-end">
                <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-xl rounded-br-sm px-4 py-3 max-w-[85%] sm:max-w-[75%]">
                  <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                    {step.user_input}
                  </p>
                </div>
              </div>
            )}

            {/* LLM response card */}
            <LLMResponse step={step} />
          </div>
        ))}

        {/* Current step: user input that was submitted but not yet completed */}
        {currentStep?.user_input && currentStep.status !== "completed" && (
          <div className="flex justify-end">
            <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-xl rounded-br-sm px-4 py-3 max-w-[85%] sm:max-w-[75%]">
              <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                {currentStep.user_input}
              </p>
            </div>
          </div>
        )}

        {/* Thinking indicator during polling */}
        {isPolling && <ThinkingIndicator />}

        {/* Completion message */}
        {isCompleted && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800 p-5 text-center animate-fade-in">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/40 mb-3">
              <svg
                className="h-5 w-5 text-green-600 dark:text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="font-medium text-green-800 dark:text-green-300">
              Анализ завершён
            </p>
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
              Все шаги АРИЗ пройдены. Перейдите к итогам для просмотра решений.
            </p>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input area (hidden when session is completed) */}
      {!isCompleted && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-2">
          <UserInput
            onSubmit={onSubmit}
            disabled={!canInput}
            stepCode={currentStep?.step_code}
            placeholder={
              isWaiting
                ? "Ожидание ответа ТРИЗ-эксперта..."
                : `Шаг ${currentStep?.step_code || ""}: ${currentStep?.step_name || "Ваш ответ..."}`
            }
          />
        </div>
      )}
    </div>
  );
}
