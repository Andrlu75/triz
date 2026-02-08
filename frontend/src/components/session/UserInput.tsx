import { FormEvent, KeyboardEvent, useRef, useState } from "react";

interface UserInputProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  stepHint?: string;
  stepCode?: string;
}

/** Contextual hints for each ARIZ express step. */
const STEP_HINTS: Record<string, string> = {
  "1": "Опишите проблемную ситуацию: что происходит, какие ограничения, что должно измениться.",
  "2": "Укажите, какое улучшение вы хотите получить и что при этом ухудшается.",
  "3": "Определите два конфликтующих требования к одному элементу системы.",
  "4": "Сформулируйте идеальный результат: что должен делать элемент сам по себе.",
  "5": "Опишите обострённое физическое противоречие: элемент должен быть X и не-X одновременно.",
  "6": "Уточните условия: когда, где, при каких обстоятельствах возникает конфликт.",
  "7": "Предложите ваше решение или выберите наиболее перспективное направление.",
};

/**
 * Textarea + submit button for user input during an ARIZ session.
 *
 * Features:
 * - Contextual hints for each ARIZ step
 * - Ctrl+Enter to submit
 * - Auto-resize textarea
 * - Disabled during LLM processing
 */
export default function UserInput({
  onSubmit,
  disabled = false,
  placeholder = "Введите ваш ответ...",
  stepHint,
  stepCode,
}: UserInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const hint = stepHint || (stepCode ? STEP_HINTS[stepCode] : undefined);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText("");
    // Reset textarea height after clearing
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    // Auto-resize: reset to auto, then set to scrollHeight (capped at 200px)
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {hint && (
        <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
          {hint}
        </p>
      )}
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={2}
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-none transition-colors"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="flex-shrink-0 px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          aria-label="Отправить"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
            />
          </svg>
        </button>
      </div>
      <p className="text-xs text-gray-400 dark:text-gray-500">
        Ctrl+Enter для отправки
      </p>
    </form>
  );
}
