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
  onSubmit: (text: string) => void;
}

export default function ChatInterface({
  steps,
  currentStep,
  isPolling,
  isSubmitting,
  onSubmit,
}: ChatInterfaceProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new content
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [steps, currentStep, isPolling]);

  const completedSteps = steps.filter(
    (s) => s.status === "completed" && s.llm_output,
  );

  const isWaiting = isPolling || isSubmitting;
  const canInput =
    currentStep?.status === "pending" && !isWaiting;

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pb-4"
      >
        {completedSteps.map((step) => (
          <div key={step.id} className="space-y-3">
            {step.user_input && (
              <div className="flex justify-end">
                <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-xl px-4 py-3 max-w-[80%]">
                  <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                    {step.user_input}
                  </p>
                </div>
              </div>
            )}
            <LLMResponse step={step} />
          </div>
        ))}

        {/* Current step's user input (if submitted but not yet completed) */}
        {currentStep?.user_input &&
          currentStep.status !== "completed" && (
            <div className="flex justify-end">
              <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-xl px-4 py-3 max-w-[80%]">
                <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
                  {currentStep.user_input}
                </p>
              </div>
            </div>
          )}

        {isPolling && <ThinkingIndicator />}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <UserInput
          onSubmit={onSubmit}
          disabled={!canInput}
          placeholder={
            isWaiting
              ? "Ожидание ответа..."
              : `Шаг ${currentStep?.step_code}: ${currentStep?.step_name || ""}`
          }
        />
      </div>
    </div>
  );
}
