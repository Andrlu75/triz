import { FormEvent, useState } from "react";

interface UserInputProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  stepHint?: string;
}

export default function UserInput({
  onSubmit,
  disabled = false,
  placeholder = "Введите ваш ответ...",
  stepHint,
}: UserInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText("");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      {stepHint && (
        <p className="text-xs text-gray-500 dark:text-gray-400">{stepHint}</p>
      )}
      <div className="flex gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          rows={3}
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="self-end px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Отправить
        </button>
      </div>
      <p className="text-xs text-gray-400">Ctrl+Enter для отправки</p>
    </form>
  );
}
