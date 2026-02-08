export default function Footer() {
  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            ТРИЗ-Решатель &mdash; AI-платформа решения изобретательских задач по
            АРИЗ-2010
          </p>
          <div className="flex items-center gap-6 text-sm text-gray-400 dark:text-gray-500">
            <span>Методология В. Петрова</span>
            <span>&copy; {new Date().getFullYear()}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
