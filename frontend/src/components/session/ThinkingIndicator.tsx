import { useEffect, useState } from "react";

const THINKING_MESSAGES = [
  "ТРИЗ-эксперт анализирует...",
  "Формулирую противоречие...",
  "Подбираю приёмы разрешения...",
  "Проверяю на ложность задачи...",
  "Применяю методологию АРИЗ...",
];

/**
 * Animated "thinking" indicator shown while LLM is processing.
 * Cycles through contextual messages to keep the user engaged.
 */
export default function ThinkingIndicator() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % THINKING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-3 p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 animate-fade-in">
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce [animation-delay:0ms]" />
        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce [animation-delay:150ms]" />
        <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce [animation-delay:300ms]" />
      </div>
      <span className="text-sm text-gray-500 dark:text-gray-400 transition-opacity duration-300">
        {THINKING_MESSAGES[messageIndex]}
      </span>
    </div>
  );
}
