import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

const PLANS = [
  {
    name: "Free",
    nameRu: "Бесплатный",
    price: "0",
    period: "навсегда",
    features: [
      "5 задач в месяц",
      "Режим Экспресс",
      "7 шагов анализа",
      "Базовый чат-интерфейс",
    ],
    limitations: [
      "Без отчётов PDF/DOCX",
      "Без командной работы",
      "Без полного АРИЗ",
    ],
    cta: "Текущий план",
    color: "border-gray-300",
    bg: "bg-white dark:bg-gray-900",
    popular: false,
  },
  {
    name: "Pro",
    nameRu: "Профессионал",
    price: "990",
    period: "/ мес",
    features: [
      "50 задач в месяц",
      "Экспресс + Автопилот",
      "Отчёты PDF и DOCX",
      "Приоритетная обработка",
      "История анализов",
    ],
    limitations: ["Без командной работы", "Без полного АРИЗ-2010"],
    cta: "Выбрать Pro",
    color: "border-primary-500",
    bg: "bg-primary-50 dark:bg-primary-900/20",
    popular: true,
  },
  {
    name: "Business",
    nameRu: "Бизнес",
    price: "4 990",
    period: "/ мес",
    features: [
      "Безлимит задач",
      "Все режимы (включая полный АРИЗ-2010)",
      "Командная работа",
      "Шаринг задач",
      "Отчёты PDF и DOCX",
      "Приоритетная поддержка",
      "API-доступ",
    ],
    limitations: [],
    cta: "Выбрать Business",
    color: "border-amber-500",
    bg: "bg-amber-50 dark:bg-amber-900/20",
    popular: false,
  },
] as const;

export default function PricingPage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
          Тарифные планы
        </h1>
        <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
          Выберите план, подходящий для ваших задач. Начните бесплатно и
          масштабируйтесь по мере необходимости.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`relative rounded-xl border-2 ${plan.color} ${plan.bg} p-6 flex flex-col`}
          >
            {plan.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                Популярный
              </span>
            )}

            <div className="mb-6">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                {plan.nameRu}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {plan.name}
              </p>
            </div>

            <div className="mb-6">
              <span className="text-4xl font-bold text-gray-900 dark:text-white">
                {plan.price} ₽
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400 ml-1">
                {plan.period}
              </span>
            </div>

            <ul className="space-y-2 mb-6 flex-1">
              {plan.features.map((f) => (
                <li
                  key={f}
                  className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                >
                  <span className="text-green-500 mt-0.5">✓</span>
                  {f}
                </li>
              ))}
              {plan.limitations.map((l) => (
                <li
                  key={l}
                  className="flex items-start gap-2 text-sm text-gray-400 dark:text-gray-500"
                >
                  <span className="mt-0.5">—</span>
                  {l}
                </li>
              ))}
            </ul>

            <button
              onClick={() =>
                navigate(isAuthenticated ? "/dashboard" : "/register")
              }
              className={`w-full py-2.5 rounded-lg text-sm font-medium transition-colors ${
                plan.popular
                  ? "bg-primary-600 text-white hover:bg-primary-700"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
