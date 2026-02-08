"""
Express mode — 7-step abbreviated ARIZ for B2C users.

Uses simple everyday language, hides TRIZ terminology.
"""
from apps.ariz_engine.steps.registry import EXPRESS_STEPS, StepDef


class ExpressMode:
    """
    Express ARIZ mode — 7 steps of the Abbreviated ARIZ.

    Steps:
        1. Problem Formulation
        2. Surface Contradiction (ПП)
        3. Deepened Contradiction (УП)
        4. Ideal Final Result (ИКР)
        5. Sharpened Contradiction (ОП)
        6. Deepening ОП (ОП₁)
        7. Solution
    """

    MODE_NAME = "express"
    AUDIENCE = "b2c"

    def get_steps(self) -> list[StepDef]:
        """Return the 7 express steps."""
        return EXPRESS_STEPS

    def get_step_count(self) -> int:
        return len(EXPRESS_STEPS)

    def format_step_name(self, step_def: StepDef) -> str:
        """Format step name for B2C audience (no TRIZ jargon)."""
        friendly_names = {
            "1": "Опишите вашу проблему",
            "2": "В чём главное затруднение?",
            "3": "Почему это сложно решить?",
            "4": "Каким должен быть идеальный результат?",
            "5": "Что мешает достичь идеала?",
            "6": "Копаем глубже: корень проблемы",
            "7": "Решение вашей задачи",
        }
        return friendly_names.get(step_def.code, step_def.name)

    def get_step_hint(self, step_code: str) -> str:
        """Return a contextual hint for the user input area."""
        hints = {
            "1": "Опишите проблему своими словами. Что происходит? Что не устраивает?",
            "2": "Что вы пытались сделать? Почему не получается?",
            "3": "Согласны ли вы с анализом? Хотите что-то уточнить?",
            "4": "Как бы выглядел идеальный вариант решения?",
            "5": "Подтвердите формулировку или предложите коррективы.",
            "6": "Есть ли дополнительные ограничения или ресурсы?",
            "7": "Оцените предложенные решения. Какое ближе к вашей ситуации?",
        }
        return hints.get(step_code, "Введите ваш ответ...")
