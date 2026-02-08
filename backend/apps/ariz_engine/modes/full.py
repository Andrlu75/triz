"""
Full ARIZ-2010 mode — complete 4-part methodology with ~24 steps.

Implementation placeholder. Full implementation in Phase 4 (task #59).
"""
from apps.ariz_engine.steps.registry import FULL_STEPS, StepDef


class FullARIZMode:
    """
    Full ARIZ-2010 mode — 4 parts, ~24 steps.

    Parts:
        1. Problem Analysis (7 steps, rules 1-16)
        2. Resource Analysis (3 steps)
        3. IKR and Physical Contradiction (6 steps)
        4. Solution (8 steps)

    Full implementation: Phase 4, task #59.
    """

    MODE_NAME = "full"
    AUDIENCE = "b2b"

    def get_steps(self) -> list[StepDef]:
        """Return all full ARIZ-2010 steps."""
        return FULL_STEPS

    def get_step_count(self) -> int:
        return len(FULL_STEPS)

    def get_part_name(self, part: int) -> str:
        """Return the name of a given ARIZ part (1-4)."""
        parts = {
            1: "Анализ задачи",
            2: "Анализ ресурсов",
            3: "Определение ИКР и ФП",
            4: "Получение решения",
        }
        return parts.get(part, f"Часть {part}")

    def get_steps_for_part(self, part: int) -> list[StepDef]:
        """Return steps belonging to a specific part."""
        prefix = f"{part}."
        return [s for s in FULL_STEPS if s.code.startswith(prefix)]
