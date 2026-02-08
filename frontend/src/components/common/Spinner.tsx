interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const SIZES = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-[3px]",
};

/**
 * Animated spinner using Tailwind CSS. Optionally shows a label below.
 */
export default function Spinner({
  size = "md",
  className = "",
  label,
}: SpinnerProps) {
  return (
    <div className={`inline-flex flex-col items-center gap-2 ${className}`}>
      <div
        className={`animate-spin border-primary-600 border-t-transparent rounded-full ${SIZES[size]}`}
        role="status"
        aria-label={label || "Loading"}
      />
      {label && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {label}
        </span>
      )}
    </div>
  );
}
