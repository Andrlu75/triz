import ReactMarkdown from "react-markdown";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Renders Markdown content using react-markdown with Tailwind prose styling.
 * Supports headings, lists, bold, italic, code blocks, links, etc.
 */
export default function MarkdownRenderer({
  content,
  className = "",
}: MarkdownRendererProps) {
  return (
    <div
      className={`prose prose-sm dark:prose-invert max-w-none
        prose-headings:text-gray-900 dark:prose-headings:text-white
        prose-p:text-gray-700 dark:prose-p:text-gray-300
        prose-strong:text-gray-900 dark:prose-strong:text-white
        prose-code:bg-gray-100 dark:prose-code:bg-gray-800
        prose-code:px-1 prose-code:py-0.5 prose-code:rounded
        prose-code:text-sm prose-code:font-mono
        prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800
        prose-pre:rounded-lg
        prose-a:text-primary-600 dark:prose-a:text-primary-400
        prose-li:text-gray-700 dark:prose-li:text-gray-300
        prose-ol:text-gray-700 dark:prose-ol:text-gray-300
        prose-ul:text-gray-700 dark:prose-ul:text-gray-300
        ${className}`}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
