"""
Step registry — single source of truth for ARIZ step definitions.

Defines the step flow for each ARIZ mode (Express, Full, Autopilot).
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StepDef:
    """Definition of a single ARIZ step."""

    code: str
    name: str
    prompt: str
    validators: list[str] = field(default_factory=list)
    description: str = ""


# ---------------------------------------------------------------------------
# Express ARIZ — 7 steps (Краткий АРИЗ)
# ---------------------------------------------------------------------------

EXPRESS_STEPS: list[StepDef] = [
    StepDef(
        code="1",
        name="Формулировка задачи",
        prompt="steps/express/step_1.j2",
        validators=["falseness_check"],
        description="Пользователь описывает проблему. Проверка на ложность.",
    ),
    StepDef(
        code="2",
        name="Поверхностное противоречие",
        prompt="steps/express/step_2.j2",
        validators=["terms_check"],
        description="Выявление поверхностного противоречия (ПП). Замена спецтерминов.",
    ),
    StepDef(
        code="3",
        name="Углублённое противоречие",
        prompt="steps/express/step_3.j2",
        validators=["contradiction_check"],
        description="Формулировка углублённого противоречия (УП).",
    ),
    StepDef(
        code="4",
        name="Идеальный конечный результат",
        prompt="steps/express/step_4.j2",
        validators=["ikr_check"],
        description="Формулировка ИКР — идеального конечного результата.",
    ),
    StepDef(
        code="5",
        name="Обострённое противоречие",
        prompt="steps/express/step_5.j2",
        validators=["conflict_check"],
        description="Формулировка обострённого противоречия (ОП).",
    ),
    StepDef(
        code="6",
        name="Углубление ОП",
        prompt="steps/express/step_6.j2",
        validators=[],
        description="Углубление обострённого противоречия (ОП₁).",
    ),
    StepDef(
        code="7",
        name="Решение",
        prompt="steps/express/step_7.j2",
        validators=[],
        description="Генерация решения на основе приёмов, эффектов, стандартов.",
    ),
]


# ---------------------------------------------------------------------------
# Full ARIZ-2010 — 4 parts, ~24 steps
# ---------------------------------------------------------------------------

FULL_STEPS: list[StepDef] = [
    # Part 1: Problem Analysis (Анализ задачи)
    StepDef(code="1.1", name="Мини-задача", prompt="steps/full/step_1_1.j2",
            validators=["falseness_check"],
            description="Записать условие мини-задачи без специальных терминов."),
    StepDef(code="1.2", name="Конфликтующая пара", prompt="steps/full/step_1_2.j2",
            validators=["terms_check"],
            description="Определить конфликтующую пару: изделие и инструмент."),
    StepDef(code="1.3", name="Графические схемы ТП-1 и ТП-2", prompt="steps/full/step_1_3.j2",
            validators=["contradiction_check"],
            description="Составить графические схемы ТП-1 и ТП-2."),
    StepDef(code="1.4", name="Выбор схемы конфликта", prompt="steps/full/step_1_4.j2",
            validators=[],
            description="Выбрать из ТП-1 и ТП-2 ту, которая обеспечивает ГФ."),
    StepDef(code="1.5", name="Усиление конфликта", prompt="steps/full/step_1_5.j2",
            validators=["conflict_check"],
            description="Усилить конфликт, указав предельное состояние."),
    StepDef(code="1.6", name="Модель задачи", prompt="steps/full/step_1_6.j2",
            validators=[],
            description="Записать формулировку модели задачи."),
    StepDef(code="1.7", name="Применение стандартов", prompt="steps/full/step_1_7.j2",
            validators=[],
            description="Проверить возможность применения системы стандартов."),

    # Part 2: Resource Analysis (Анализ ресурсов)
    StepDef(code="2.1", name="Оперативная зона", prompt="steps/full/step_2_1.j2",
            validators=[],
            description="Определить оперативную зону (ОЗ)."),
    StepDef(code="2.2", name="Оперативное время", prompt="steps/full/step_2_2.j2",
            validators=[],
            description="Определить оперативное время (ОВ)."),
    StepDef(code="2.3", name="Вещественно-полевые ресурсы", prompt="steps/full/step_2_3.j2",
            validators=[],
            description="Определить ВПР (вещественно-полевые ресурсы)."),

    # Part 3: IKR Definition (Определение ИКР и ФП)
    StepDef(code="3.1", name="Формулировка ИКР-1", prompt="steps/full/step_3_1.j2",
            validators=["ikr_check"],
            description="Записать формулировку ИКР-1."),
    StepDef(code="3.2", name="Усиление ИКР-1", prompt="steps/full/step_3_2.j2",
            validators=[],
            description="Усилить формулировку ИКР-1."),
    StepDef(code="3.3", name="Макро-уровень ФП", prompt="steps/full/step_3_3.j2",
            validators=[],
            description="Определить ФП на макро-уровне."),
    StepDef(code="3.4", name="Микро-уровень ФП", prompt="steps/full/step_3_4.j2",
            validators=[],
            description="Определить ФП на микро-уровне."),
    StepDef(code="3.5", name="Формулировка ИКР-2", prompt="steps/full/step_3_5.j2",
            validators=["ikr_check"],
            description="Записать формулировку ИКР-2."),
    StepDef(code="3.6", name="Проверка ФП", prompt="steps/full/step_3_6.j2",
            validators=[],
            description="Проверить возможность устранения ФП."),

    # Part 4: Solution (Получение решения)
    StepDef(code="4.1", name="Метод ММЧ", prompt="steps/full/step_4_1.j2",
            validators=[],
            description="Использовать метод моделирования маленькими человечками."),
    StepDef(code="4.2", name="Шаг назад от ИКР", prompt="steps/full/step_4_2.j2",
            validators=[],
            description="Сделать шаг назад от ИКР."),
    StepDef(code="4.3", name="Применение стандартов (повторно)", prompt="steps/full/step_4_3.j2",
            validators=[],
            description="Применить стандарты на решение изобретательских задач."),
    StepDef(code="4.4", name="Применение эффектов", prompt="steps/full/step_4_4.j2",
            validators=[],
            description="Применить физические, химические, геометрические эффекты."),
    StepDef(code="4.5", name="Использование ресурсов", prompt="steps/full/step_4_5.j2",
            validators=[],
            description="Использовать выявленные ВПР."),
    StepDef(code="4.6", name="Изменение задачи", prompt="steps/full/step_4_6.j2",
            validators=[],
            description="Если задача не решена — изменить или переформулировать."),
    StepDef(code="4.7", name="Проверка решения", prompt="steps/full/step_4_7.j2",
            validators=[],
            description="Проверить полученное решение по критериям."),
    StepDef(code="4.8", name="Применение решения", prompt="steps/full/step_4_8.j2",
            validators=[],
            description="Оценить применимость и масштабирование решения."),
]


# ---------------------------------------------------------------------------
# Step lookup helpers
# ---------------------------------------------------------------------------

_EXPRESS_MAP: dict[str, StepDef] = {s.code: s for s in EXPRESS_STEPS}
_FULL_MAP: dict[str, StepDef] = {s.code: s for s in FULL_STEPS}

MODE_STEPS: dict[str, list[StepDef]] = {
    "express": EXPRESS_STEPS,
    "full": FULL_STEPS,
    "autopilot": EXPRESS_STEPS,  # Autopilot uses express step definitions
}


def get_steps_for_mode(mode: str) -> list[StepDef]:
    """Return the list of steps for a given ARIZ mode."""
    return MODE_STEPS.get(mode, EXPRESS_STEPS)


def get_step_def(mode: str, code: str) -> StepDef | None:
    """Look up a single step definition by mode and code."""
    step_map = _EXPRESS_MAP if mode in ("express", "autopilot") else _FULL_MAP
    return step_map.get(code)


def get_next_step(mode: str, current_code: str) -> StepDef | None:
    """Return the next step after the given code, or None if at the end."""
    steps = get_steps_for_mode(mode)
    for i, step in enumerate(steps):
        if step.code == current_code and i + 1 < len(steps):
            return steps[i + 1]
    return None


def get_previous_step(mode: str, current_code: str) -> StepDef | None:
    """Return the previous step before the given code, or None if at the start."""
    steps = get_steps_for_mode(mode)
    for i, step in enumerate(steps):
        if step.code == current_code and i > 0:
            return steps[i - 1]
    return None
