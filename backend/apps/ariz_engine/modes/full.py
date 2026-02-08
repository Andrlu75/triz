"""
Full ARIZ-2010 mode -- complete 4-part methodology with ~24 steps.

Implements the complete Algorithm for Inventive Problem Solving (ARIZ-2010)
as described by Vladimir Petrov. Designed for B2B audience with full TRIZ
terminology.

Parts:
    1. Problem Analysis (steps 1.1-1.7, rules 1-16)
    2. Resource Analysis (steps 2.1-2.3)
    3. IKR and Physical Contradiction (steps 3.1-3.6)
    4. Solution (steps 4.1-4.8, knowledge base integration)
"""
import logging
from typing import Any

from apps.ariz_engine.models import (
    ARIZSession,
    Contradiction,
    IKR,
    Solution,
    StepResult,
)
from apps.ariz_engine.steps.registry import FULL_STEPS, StepDef
from apps.ariz_engine.validators.base import validate_step_output

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Part definitions
# ---------------------------------------------------------------------------

PART_DEFINITIONS: dict[int, dict[str, Any]] = {
    1: {
        "name": "Анализ задачи",
        "name_en": "Problem Analysis",
        "description": (
            "Анализ исходной ситуации, определение конфликтующей пары, "
            "построение модели задачи. Правила 1-16 АРИЗ."
        ),
        "rules": list(range(1, 17)),
        "step_range": ("1.1", "1.7"),
    },
    2: {
        "name": "Анализ ресурсов",
        "name_en": "Resource Analysis",
        "description": (
            "Определение оперативной зоны, оперативного времени и "
            "вещественно-полевых ресурсов (ВПР)."
        ),
        "rules": [],
        "step_range": ("2.1", "2.3"),
    },
    3: {
        "name": "Определение ИКР и ФП",
        "name_en": "IKR and Physical Contradiction",
        "description": (
            "Формулировка идеального конечного результата (ИКР-1, ИКР-2), "
            "определение физического противоречия (ФП) на макро- и микро-уровне."
        ),
        "rules": list(range(17, 26)),
        "step_range": ("3.1", "3.6"),
    },
    4: {
        "name": "Получение решения",
        "name_en": "Solution",
        "description": (
            "Применение методов разрешения ФП: ММЧ, шаг назад от ИКР, "
            "стандарты, эффекты, ВПР. Проверка и оценка решения."
        ),
        "rules": list(range(26, 29)),
        "step_range": ("4.1", "4.8"),
    },
}

# Steps that require knowledge base integration (Part 4)
KNOWLEDGE_BASE_STEPS = {"4.1", "4.3", "4.4", "4.5", "4.7", "4.8"}

# Mapping of steps to the TRIZ rules they primarily enforce
STEP_RULES: dict[str, list[int]] = {
    "1.1": [1, 2, 3],
    "1.2": [4, 5, 6, 7, 8, 9, 10, 11],
    "1.3": [12, 13, 14],
    "1.4": [4, 5, 6],
    "1.5": [12, 13],
    "1.6": [15, 16],
    "1.7": [],
    "2.1": [],
    "2.2": [],
    "2.3": [],
    "3.1": [17, 18],
    "3.2": [19, 20],
    "3.3": [21, 22],
    "3.4": [23, 24],
    "3.5": [17, 18],
    "3.6": [25],
    "4.1": [26],
    "4.2": [],
    "4.3": [],
    "4.4": [],
    "4.5": [],
    "4.6": [],
    "4.7": [27],
    "4.8": [28],
}

# B2B step hints (professional TRIZ terminology)
STEP_HINTS: dict[str, str] = {
    "1.1": (
        "Запишите условие мини-задачи: техническая система, её назначение "
        "(главная функция), нежелательный эффект. Не используйте специальные "
        "термины (правило 15)."
    ),
    "1.2": (
        "Определите конфликтующую пару элементов: инструмент (элемент, "
        "который можно изменять) и изделие (элемент, который нельзя менять). "
        "Укажите главную функцию инструмента."
    ),
    "1.3": (
        "Составьте графические схемы ТП-1 и ТП-2. Для каждого технического "
        "противоречия укажите: что улучшается и что ухудшается."
    ),
    "1.4": (
        "Выберите из ТП-1 и ТП-2 то противоречие, разрешение которого "
        "обеспечивает наилучшее выполнение главной функции системы."
    ),
    "1.5": (
        "Усильте выбранный конфликт до предельного состояния. Введите "
        "в формулировку X-элемент -- элемент, способный устранить НЭ."
    ),
    "1.6": (
        "Запишите формулировку модели задачи: конфликтующая пара + усиленная "
        "формулировка + что должен обеспечить X-элемент."
    ),
    "1.7": (
        "Проверьте, решается ли задача применением системы стандартов на "
        "решение изобретательских задач (76 стандартов, 5 классов)."
    ),
    "2.1": (
        "Определите оперативную зону (ОЗ) -- область, в которой возникает "
        "конфликт. ОЗ = зона инструмента + зона изделия."
    ),
    "2.2": (
        "Определите оперативное время (ОВ): Т1 -- время конфликтного "
        "действия, Т2 -- время до конфликта, Т3 -- время после конфликта."
    ),
    "2.3": (
        "Определите вещественно-полевые ресурсы (ВПР): внутрисистемные, "
        "внешнесистемные, надсистемные. Для каждого -- вещественные и полевые."
    ),
    "3.1": (
        "Сформулируйте ИКР-1 по шаблону: X-элемент в оперативной зоне "
        "в течение оперативного времени САМ устраняет НЭ, сохраняя ГФ."
    ),
    "3.2": (
        "Усильте формулировку ИКР-1: что должно быть в ОЗ вместо X-элемента? "
        "Идеально: в системе ничего нового, а НЭ устранён."
    ),
    "3.3": (
        "Определите физическое противоречие (ФП) на макро-уровне: часть ОЗ "
        "должна обладать свойством [+A] для обеспечения ГФ и свойством [-A] "
        "для устранения НЭ."
    ),
    "3.4": (
        "Определите ФП на микро-уровне: частицы вещества в ОЗ должны быть "
        "в состоянии [C] для обеспечения ГФ и в состоянии [анти-C] для "
        "устранения НЭ."
    ),
    "3.5": (
        "Сформулируйте ИКР-2: ОЗ САМА обеспечивает противоположные "
        "физические свойства в течение ОВ."
    ),
    "3.6": (
        "Проверьте, можно ли устранить ФП применением типовых преобразований: "
        "разделение в пространстве, во времени, в структуре, системный переход."
    ),
    "4.1": (
        "Используйте метод моделирования маленькими человечками (ММЧ) "
        "для визуализации конфликта и поиска решения."
    ),
    "4.2": (
        "Сделайте шаг назад от ИКР: если ИКР недостижим, рассмотрите "
        "ближайшее к нему решение."
    ),
    "4.3": (
        "Повторно проверьте возможность применения стандартов на решение "
        "изобретательских задач (76 стандартов) к модели задачи из Части 3."
    ),
    "4.4": (
        "Примените физические, химические, биологические, геометрические "
        "эффекты для устранения физического противоречия."
    ),
    "4.5": (
        "Используйте выявленные ВПР (из Части 2) для разрешения ФП. "
        "Приоритет: внутрисистемные > внешнесистемные > надсистемные."
    ),
    "4.6": (
        "Если задача не решена -- переформулируйте задачу: измените "
        "мини-задачу, пересмотрите конфликтующую пару, вернитесь к Части 1."
    ),
    "4.7": (
        "Проверьте полученное решение: не создаёт ли оно новых противоречий? "
        "Соответствует ли ИКР? Использует ли ВПР? Правило 27."
    ),
    "4.8": (
        "Оцените применимость решения: новизна, реализуемость, идеальность. "
        "Обобщите опыт для базы знаний. Сформулируйте задачу-аналог. Правило 28."
    ),
}

# Mapping step codes to context_snapshot keys for aggregated context
CONTEXT_KEY_MAP: dict[str, str] = {
    "1.1": "mini_task",
    "1.2": "conflicting_pair",
    "1.3": "tp_schemas",
    "1.4": "selected_tp",
    "1.5": "amplified_conflict",
    "1.6": "task_model",
    "1.7": "standards_applicable",
    "2.1": "operative_zone",
    "2.2": "operative_time",
    "2.3": "vpr_list",
    "3.1": "ikr_1",
    "3.2": "ikr_1_strengthened",
    "3.3": "fp_macro",
    "3.4": "fp_micro",
    "3.5": "ikr_2",
    "3.6": "fp_resolution_check",
    "4.1": "mmch_model",
    "4.2": "step_back_from_ikr",
    "4.3": "standards_result",
    "4.4": "effects_applied",
    "4.5": "vpr_utilization",
    "4.6": "task_reformulated",
    "4.7": "solution_verification",
    "4.8": "solution_evaluation",
}

# Steps that produce Contradiction entities
CONTRADICTION_STEPS: dict[str, str] = {
    "1.3": "surface",      # TP schemas -> surface contradiction
    "1.5": "deepened",      # Amplified conflict -> deepened contradiction
    "3.1": "sharpened",     # FP macro level -> sharpened contradiction
    "3.3": "sharpened",     # FP macro level (explicit) -> sharpened
    "3.4": "sharpened",     # FP micro level -> sharpened
}

# Steps that produce IKR entities
IKR_STEPS = {"3.1", "3.2", "3.5"}

# Steps that produce Solution entities
SOLUTION_STEPS: dict[str, str] = {
    "4.1": "combined",     # MMCh method
    "4.2": "combined",     # Step back from IKR
    "4.3": "standard",     # Standards application
    "4.4": "effect",       # Effects application
    "4.5": "combined",     # VPR utilization
    "4.7": "combined",     # Solution verification
    "4.8": "combined",     # Solution evaluation
}


class FullARIZMode:
    """
    Full ARIZ-2010 mode -- 4 parts, ~24 steps.

    Implements the complete Algorithm for Inventive Problem Solving per
    V. Petrov's ARIZ-2010 methodology. Designed for B2B professionals
    with deep TRIZ expertise.

    Parts:
        1. Problem Analysis (steps 1.1-1.7, rules 1-16)
           - Mini-task formulation with falseness check
           - Conflicting pair identification (instrument + product)
           - Technical contradictions TP-1 and TP-2
           - Conflict scheme selection and amplification
           - Task model formulation
           - Standard applicability check

        2. Resource Analysis (steps 2.1-2.3)
           - Operative zone (OZ) definition
           - Operative time (OT) definition
           - Substance-field resources (VPR) inventory

        3. IKR and Physical Contradiction (steps 3.1-3.6)
           - IKR-1 formulation and strengthening
           - Physical contradiction (FP) at macro and micro levels
           - IKR-2 formulation
           - FP resolution check via standard transformations

        4. Solution (steps 4.1-4.8)
           - MMCh method (little people modeling)
           - Step back from IKR
           - Standards application (repeated)
           - Effects application (physical, chemical, bio, geometrical)
           - VPR utilization
           - Task reformulation (if needed)
           - Solution verification (rule 27)
           - Solution evaluation and generalization (rule 28)

    Knowledge base integration in Part 4:
        Steps 4.1, 4.3, 4.4, 4.5, 4.7, 4.8 query TRIZKnowledgeSearch for
        analog tasks, inventive principles, technological effects.
    """

    MODE_NAME = "full"
    AUDIENCE = "b2b"
    TOTAL_PARTS = 4

    def __init__(self) -> None:
        self._knowledge_search = None

    # ------------------------------------------------------------------
    # Knowledge base integration
    # ------------------------------------------------------------------

    def _get_knowledge_search(self):
        """Lazy-load TRIZKnowledgeSearch to avoid circular imports."""
        if self._knowledge_search is None:
            from apps.knowledge_base.search import TRIZKnowledgeSearch
            self._knowledge_search = TRIZKnowledgeSearch()
        return self._knowledge_search

    def get_knowledge_context(self, step_code: str, session_context: dict) -> dict:
        """
        Query the knowledge base for context relevant to a given step.

        Called during Part 4 steps to enrich prompts with analog tasks,
        principles, effects, and standards from the TRIZ knowledge base.

        Args:
            step_code: The current step code (e.g. "4.1", "4.4").
            session_context: Aggregated context from the session snapshot
                containing fields like ``op_formulation``, ``contradiction_type``,
                ``fp_formulation``, ``vpr_list``, etc.

        Returns:
            Dict with knowledge base results keyed by type:
            ``analog_tasks``, ``principles``, ``effects``.
        """
        if step_code not in KNOWLEDGE_BASE_STEPS:
            return {}

        kb = self._get_knowledge_search()
        knowledge_ctx: dict[str, Any] = {}

        try:
            # Analog tasks -- search by OP (sharpened contradiction) formulation
            op_formulation = session_context.get("op_formulation", "")
            fp_formulation = session_context.get("fp_formulation", "")
            search_text = op_formulation or fp_formulation

            if search_text and step_code in ("4.1", "4.3", "4.7", "4.8"):
                analogs = kb.search_analog_tasks(search_text, top_k=5)
                knowledge_ctx["analog_tasks"] = [
                    {
                        "title": a.title,
                        "problem": a.problem_description,
                        "op_formulation": a.op_formulation,
                        "solution": a.solution_principle,
                        "domain": a.domain,
                    }
                    for a in analogs
                ]

            # Inventive principles -- suggest based on contradiction type
            contradiction_type = session_context.get("contradiction_type", "sharpened")
            contradiction_formulation = session_context.get(
                "contradiction_formulation", ""
            )

            if step_code in ("4.3", "4.5", "4.7"):
                principles = kb.suggest_principles(
                    contradiction_type=contradiction_type,
                    formulation=contradiction_formulation or search_text,
                )
                knowledge_ctx["principles"] = [
                    {
                        "number": p.number,
                        "name": p.name,
                        "description": p.description,
                        "examples": p.examples,
                    }
                    for p in principles
                ]

            # Technological effects -- search by function description
            function_description = session_context.get("function_description", "")
            if not function_description:
                function_description = session_context.get("main_function", "")

            if function_description and step_code in ("4.4", "4.5"):
                effects = kb.find_effects(function_description, top_k=5)
                knowledge_ctx["effects"] = [
                    {
                        "type": e.type,
                        "name": e.name,
                        "description": e.description,
                    }
                    for e in effects
                ]

        except Exception:
            logger.exception(
                "Knowledge base query failed for step %s", step_code
            )

        return knowledge_ctx

    # ------------------------------------------------------------------
    # Step management
    # ------------------------------------------------------------------

    def get_steps(self) -> list[StepDef]:
        """Return all full ARIZ-2010 steps (~24 steps across 4 parts)."""
        return FULL_STEPS

    def get_step_count(self) -> int:
        """Return total number of steps."""
        return len(FULL_STEPS)

    def get_step_by_code(self, code: str) -> StepDef | None:
        """Look up a single step definition by its code."""
        for step in FULL_STEPS:
            if step.code == code:
                return step
        return None

    # ------------------------------------------------------------------
    # Part management
    # ------------------------------------------------------------------

    def get_part_name(self, part: int) -> str:
        """Return the Russian name of a given ARIZ part (1-4)."""
        defn = PART_DEFINITIONS.get(part)
        if defn:
            return defn["name"]
        return f"Часть {part}"

    def get_part_description(self, part: int) -> str:
        """Return a detailed description of the ARIZ part."""
        defn = PART_DEFINITIONS.get(part)
        if defn:
            return defn["description"]
        return ""

    def get_part_for_step(self, step_code: str) -> int:
        """Determine which part (1-4) a step belongs to."""
        if "." in step_code:
            return int(step_code.split(".")[0])
        return 1

    def get_steps_for_part(self, part: int) -> list[StepDef]:
        """Return steps belonging to a specific part."""
        prefix = f"{part}."
        return [s for s in FULL_STEPS if s.code.startswith(prefix)]

    def get_part_progress(self, part: int, completed_codes: set[str]) -> dict:
        """
        Calculate progress within a specific part.

        Args:
            part: Part number (1-4).
            completed_codes: Set of completed step codes.

        Returns:
            Dict with steps_total, steps_completed, percent.
        """
        part_steps = self.get_steps_for_part(part)
        total = len(part_steps)
        completed = sum(1 for s in part_steps if s.code in completed_codes)
        percent = round(completed / total * 100) if total > 0 else 0

        return {
            "part": part,
            "name": self.get_part_name(part),
            "steps_total": total,
            "steps_completed": completed,
            "percent": percent,
            "is_complete": completed == total,
        }

    def get_full_progress(self, completed_codes: set[str]) -> dict:
        """
        Return progress for all 4 parts plus overall.

        Args:
            completed_codes: Set of completed step codes.

        Returns:
            Dict with parts (list of part progress dicts) and overall progress.
        """
        parts = []
        for part_num in range(1, self.TOTAL_PARTS + 1):
            parts.append(self.get_part_progress(part_num, completed_codes))

        total = len(FULL_STEPS)
        total_completed = sum(1 for s in FULL_STEPS if s.code in completed_codes)
        overall_percent = round(total_completed / total * 100) if total > 0 else 0

        return {
            "parts": parts,
            "total_steps": total,
            "total_completed": total_completed,
            "overall_percent": overall_percent,
        }

    # ------------------------------------------------------------------
    # Step context & formatting (B2B)
    # ------------------------------------------------------------------

    def get_step_hint(self, step_code: str) -> str:
        """
        Return a contextual hint for the user input area (B2B professional language).

        Args:
            step_code: The step code (e.g. "1.1").

        Returns:
            Hint string with TRIZ terminology.
        """
        return STEP_HINTS.get(step_code, "Введите ваш ответ...")

    def format_step_name(self, step_def: StepDef) -> str:
        """
        Format step name for B2B audience with full TRIZ terminology.

        Shows part number, step number, and professional step name.
        """
        part = self.get_part_for_step(step_def.code)
        part_name = self.get_part_name(part)
        return f"Часть {part} ({part_name}) -- Шаг {step_def.code}: {step_def.name}"

    def get_step_rules(self, step_code: str) -> list[int]:
        """
        Return the list of ARIZ rule numbers applicable to a given step.

        Args:
            step_code: The step code.

        Returns:
            List of rule numbers (e.g. [1, 2, 3] for step 1.1).
        """
        return STEP_RULES.get(step_code, [])

    def requires_knowledge_base(self, step_code: str) -> bool:
        """Check if a step requires knowledge base queries."""
        return step_code in KNOWLEDGE_BASE_STEPS

    def get_prompt_context(self, step_code: str, session_context: dict) -> dict:
        """
        Build the full prompt context for a step, including knowledge base data.

        This method is called by the engine/task before rendering the Jinja2
        template. It enriches the session context with:
        - Part information (name, description, progress)
        - Applicable rules
        - Knowledge base results (for Part 4 steps)
        - B2B formatting hints

        Args:
            step_code: The step code.
            session_context: Aggregated context snapshot from the session.

        Returns:
            Enriched context dict ready for Jinja2 template rendering.
        """
        context = dict(session_context)

        # Add part information
        part_num = self.get_part_for_step(step_code)
        context["part_number"] = part_num
        context["part_name"] = self.get_part_name(part_num)
        context["part_description"] = self.get_part_description(part_num)

        # Add step metadata
        step_def = self.get_step_by_code(step_code)
        if step_def:
            context["step_code"] = step_def.code
            context["step_name"] = step_def.name
            context["step_description"] = step_def.description
            context["total_steps"] = self.get_step_count()

        # Add applicable rules
        context["applicable_rules"] = self.get_step_rules(step_code)

        # Add step position info
        part_steps = self.get_steps_for_part(part_num)
        step_index_in_part = 0
        for i, s in enumerate(part_steps):
            if s.code == step_code:
                step_index_in_part = i
                break
        context["step_in_part"] = step_index_in_part + 1
        context["total_steps_in_part"] = len(part_steps)

        # Global step position
        for i, s in enumerate(FULL_STEPS):
            if s.code == step_code:
                context["global_step_index"] = i + 1
                break

        # Knowledge base context (Part 4 only)
        if self.requires_knowledge_base(step_code):
            kb_context = self.get_knowledge_context(step_code, session_context)
            context["knowledge_base"] = kb_context

        return context

    def validate_transition(self, from_code: str, to_code: str) -> bool:
        """
        Validate that a step transition is allowed.

        In full ARIZ mode, steps must be completed sequentially within
        each part. Step 4.6 (task reformulation) may loop back to Part 1.

        Args:
            from_code: Current step code.
            to_code: Target step code.

        Returns:
            True if the transition is valid.
        """
        # Special case: step 4.6 can loop back to 1.1
        if from_code == "4.6" and to_code == "1.1":
            return True

        # Normal sequential progression
        step_codes = [s.code for s in FULL_STEPS]
        try:
            from_idx = step_codes.index(from_code)
            to_idx = step_codes.index(to_code)
        except ValueError:
            return False

        # Allow forward by exactly 1 step, or backward by any amount
        return to_idx == from_idx + 1 or to_idx < from_idx

    def should_apply_standards_check(self, step_code: str) -> bool:
        """
        Check if the current step should include standards applicability check.

        Steps 1.7 and 4.3 explicitly check standards. Other steps may also
        benefit from a standards check if the session context suggests it.
        """
        return step_code in ("1.7", "4.3")

    def get_part_summary_fields(self, part: int) -> list[str]:
        """
        Return the list of context fields that should be summarized
        at the end of a given part (for context_snapshot update).
        """
        fields_by_part: dict[int, list[str]] = {
            1: [
                "mini_task",
                "conflicting_pair",
                "instrument",
                "product",
                "main_function",
                "tp1_scheme",
                "tp2_scheme",
                "selected_tp",
                "amplified_conflict",
                "task_model",
                "standards_applicable",
            ],
            2: [
                "operative_zone",
                "operative_time",
                "t1_conflict_time",
                "t2_before_conflict",
                "t3_after_conflict",
                "vpr_internal",
                "vpr_external",
                "vpr_supersystem",
            ],
            3: [
                "ikr_1",
                "ikr_1_strengthened",
                "fp_macro",
                "fp_micro",
                "ikr_2",
                "fp_resolution_check",
                "fp_resolution_method",
            ],
            4: [
                "mmch_model",
                "step_back_from_ikr",
                "standards_result",
                "effects_applied",
                "vpr_utilization",
                "task_reformulated",
                "solution_verification",
                "solution_evaluation",
                "analog_task_formulation",
            ],
        }
        return fields_by_part.get(part, [])

    # ------------------------------------------------------------------
    # Step result processing & entity extraction
    # ------------------------------------------------------------------

    def process_step_result(
        self,
        session: ARIZSession,
        step_code: str,
        llm_output: str,
        user_input: str,
    ) -> dict[str, Any]:
        """
        Process the LLM output for a completed step.

        Performs validation, extracts structured entities (Contradiction,
        IKR, Solution), updates the session context snapshot, and returns
        a structured result dictionary.

        Args:
            session: The ARIZ session.
            step_code: The step that was completed.
            llm_output: The raw LLM response text.
            user_input: The user's original input for this step.

        Returns:
            Dict with validated_result, validation_results,
            extracted entities, and context update status.
        """
        step_def = self.get_step_by_code(step_code)
        if step_def is None:
            raise ValueError(f"Unknown step code: {step_code}")

        # Run validators
        validation_results: list[dict] = []
        if step_def.validators:
            validation_results = validate_step_output(
                validator_names=step_def.validators,
                content=llm_output,
                context={"audience": self.AUDIENCE, "mode": self.MODE_NAME},
            )

        all_valid = all(r.get("valid", True) for r in validation_results)

        # Build validation notes text
        validation_notes = ""
        if validation_results:
            note_parts = []
            for vr in validation_results:
                validator_name = vr.get("validator", "")
                if vr.get("valid"):
                    note_parts.append(f"[{validator_name}] OK")
                else:
                    issues = "; ".join(vr.get("issues", []))
                    note_parts.append(f"[{validator_name}] FAIL: {issues}")
            validation_notes = " | ".join(note_parts)

        # Update session context snapshot
        context_key = CONTEXT_KEY_MAP.get(step_code)
        if context_key:
            snapshot = dict(session.context_snapshot or {})
            snapshot[context_key] = llm_output[:3000]
            session.context_snapshot = snapshot
            session.save(update_fields=["context_snapshot"])

        # Extract entities
        entities = self._extract_entities(session, step_code, llm_output)

        return {
            "step_code": step_code,
            "step_name": step_def.name,
            "part": self.get_part_for_step(step_code),
            "validated_result": llm_output,
            "validation_results": validation_results,
            "validation_notes": validation_notes,
            "all_valid": all_valid,
            "entities": entities,
        }

    def _extract_entities(
        self,
        session: ARIZSession,
        step_code: str,
        llm_output: str,
    ) -> dict[str, Any]:
        """
        Extract structured entities from a step's LLM output.

        Creates Contradiction, IKR, and Solution model instances as
        appropriate for the given step.

        Args:
            session: The ARIZ session.
            step_code: The step code.
            llm_output: The LLM output text.

        Returns:
            Dict describing which entities were created/updated.
        """
        entities: dict[str, Any] = {}

        # Contradiction extraction
        if step_code in CONTRADICTION_STEPS:
            contradiction = self._extract_contradiction(
                session, step_code, llm_output
            )
            if contradiction:
                entities["contradiction"] = {
                    "id": contradiction.pk,
                    "type": contradiction.type,
                    "formulation": contradiction.formulation[:200],
                }

        # IKR extraction
        if step_code in IKR_STEPS:
            ikr = self._extract_ikr(session, step_code, llm_output)
            if ikr:
                entities["ikr"] = {
                    "id": ikr.pk,
                    "formulation": ikr.formulation[:200],
                }

        # Solution extraction
        if step_code in SOLUTION_STEPS:
            solution = self._extract_solution(session, step_code, llm_output)
            if solution:
                entities["solution"] = {
                    "id": solution.pk,
                    "title": solution.title,
                    "method_used": solution.method_used,
                }

        return entities

    def _extract_contradiction(
        self,
        session: ARIZSession,
        step_code: str,
        llm_output: str,
    ) -> Contradiction | None:
        """
        Extract and persist a Contradiction from the LLM output.

        Parses the output for property S and anti-S by keyword heuristics,
        and creates or updates the Contradiction record.
        """
        contradiction_type = CONTRADICTION_STEPS.get(step_code)
        if not contradiction_type:
            return None

        # Heuristic extraction of S / anti-S properties from output
        property_s = ""
        anti_property_s = ""
        quality_a = ""
        quality_b = ""

        for line in llm_output.split("\n"):
            stripped = line.strip().lower()
            raw_value = line.split(":", 1)[-1].strip() if ":" in line else ""

            if any(
                kw in stripped
                for kw in ["свойство s:", "свойство:", "property s:"]
            ):
                property_s = raw_value[:255]
            elif any(
                kw in stripped
                for kw in [
                    "анти-свойство:", "анти-s:", "anti-s:", "anti-property:",
                ]
            ):
                anti_property_s = raw_value[:255]
            elif "тп-1:" in stripped or "tp-1:" in stripped:
                quality_a = raw_value[:255]
            elif "тп-2:" in stripped or "tp-2:" in stripped:
                quality_b = raw_value[:255]

        contradiction, created = Contradiction.objects.update_or_create(
            session=session,
            type=contradiction_type,
            defaults={
                "formulation": llm_output[:2000],
                "property_s": property_s,
                "anti_property_s": anti_property_s,
                "quality_a": quality_a,
                "quality_b": quality_b,
            },
        )

        logger.info(
            "Contradiction %s (%s) for session %d — created=%s",
            contradiction_type,
            step_code,
            session.pk,
            created,
        )
        return contradiction

    def _extract_ikr(
        self,
        session: ARIZSession,
        step_code: str,
        llm_output: str,
    ) -> IKR | None:
        """
        Extract and persist an IKR record from the LLM output.

        Steps 3.1/3.2 produce IKR-1. Step 3.5 produces IKR-2.
        """
        snapshot = session.context_snapshot or {}
        vpr_data = snapshot.get("vpr_list", "")
        vpr_list = [vpr_data] if vpr_data else []

        if step_code in ("3.1", "3.2"):
            label = "ИКР-1"
            defaults = {
                "formulation": f"{label}: {llm_output[:1500]}",
                "vpr_used": vpr_list,
            }
            if step_code == "3.2":
                defaults["strengthened_formulation"] = llm_output[:1500]

            ikr, created = IKR.objects.update_or_create(
                session=session,
                formulation__startswith=label,
                defaults=defaults,
            )
            logger.info(
                "IKR-1 for session %d — step %s, created=%s",
                session.pk,
                step_code,
                created,
            )
            return ikr

        if step_code == "3.5":
            label = "ИКР-2"
            ikr, created = IKR.objects.update_or_create(
                session=session,
                formulation__startswith=label,
                defaults={
                    "formulation": f"{label}: {llm_output[:1500]}",
                    "strengthened_formulation": "",
                    "vpr_used": vpr_list,
                },
            )
            logger.info(
                "IKR-2 for session %d — step %s, created=%s",
                session.pk,
                step_code,
                created,
            )
            return ikr

        return None

    def _extract_solution(
        self,
        session: ARIZSession,
        step_code: str,
        llm_output: str,
    ) -> Solution | None:
        """
        Extract and persist a Solution from the LLM output.

        Different steps map to different solution methods.
        """
        method = SOLUTION_STEPS.get(step_code)
        if not method:
            return None

        step_def = self.get_step_by_code(step_code)
        default_title = (
            f"Решение (шаг {step_code}: {step_def.name})"
            if step_def
            else f"Решение (шаг {step_code})"
        )

        # Extract a meaningful title from the first non-trivial line
        title = default_title
        for line in llm_output.split("\n"):
            stripped = line.strip()
            if (
                stripped
                and len(stripped) > 10
                and not stripped.startswith(("#", "```", "---", "**"))
            ):
                title = stripped[:255]
                break

        solution = Solution.objects.create(
            session=session,
            method_used=method,
            title=title,
            description=llm_output[:5000],
            novelty_score=5,
            feasibility_score=5,
        )

        logger.info(
            "Solution created for session %d — step %s, method=%s",
            session.pk,
            step_code,
            method,
        )
        return solution

    # ------------------------------------------------------------------
    # Response formatting (B2B)
    # ------------------------------------------------------------------

    def format_response(self, step_code: str, llm_output: str) -> str:
        """
        Format the LLM response for B2B display.

        Prepends a structured header with part name, step name,
        applicable rules, and step position information.

        Args:
            step_code: The current step code.
            llm_output: The raw LLM output to format.

        Returns:
            Formatted response string with professional TRIZ header.
        """
        step_def = self.get_step_by_code(step_code)
        if step_def is None:
            return llm_output

        part = self.get_part_for_step(step_code)
        part_name = self.get_part_name(part)

        # Part and step header
        parts = [
            f"### Часть {part}: {part_name}",
            f"#### Шаг {step_code}: {step_def.name}",
            "",
        ]

        # Applicable rules
        rules = self.get_step_rules(step_code)
        if rules:
            rules_str = ", ".join(str(r) for r in rules)
            parts.append(f"**Правила АРИЗ:** {rules_str}")
            parts.append("")

        # Step position
        part_steps = self.get_steps_for_part(part)
        step_in_part = 0
        for i, s in enumerate(part_steps):
            if s.code == step_code:
                step_in_part = i + 1
                break
        parts.append(
            f"*Шаг {step_in_part} из {len(part_steps)} в Части {part} "
            f"({self.get_step_count()} шагов всего)*"
        )
        parts.append("")
        parts.append("---")
        parts.append("")

        header = "\n".join(parts)
        return header + llm_output

    # ------------------------------------------------------------------
    # Transition and loop-back logic
    # ------------------------------------------------------------------

    def should_loop_back(
        self, step_code: str, llm_output: str
    ) -> str | None:
        """
        Determine if the session should loop back to an earlier step.

        ARIZ-2010 defines specific conditions where the analyst must
        return to earlier parts:

        - Step 1.7: If standards solve the task, the session could end
          early, but in full mode we continue for completeness.
        - Step 3.6: If the FP cannot be resolved by standard
          transformations, return to step 1.1 with a new formulation.
        - Step 4.6: If no solution is found after all Part 4 methods,
          return to step 1.1 to reformulate the problem.

        Args:
            step_code: The current step code.
            llm_output: The LLM output for this step.

        Returns:
            Step code to loop back to, or None to continue forward.
        """
        output_lower = llm_output.lower()

        if step_code == "3.6":
            loop_back_markers = [
                "невозможно устранить",
                "фп не разрешимо",
                "не удаётся разрешить",
                "вернуться к шагу 1",
                "переформулировать задачу",
                "возврат к части 1",
            ]
            if any(marker in output_lower for marker in loop_back_markers):
                logger.info(
                    "Step 3.6: FP cannot be resolved, "
                    "recommending loop back to 1.1"
                )
                return "1.1"

        if step_code == "4.6":
            loop_back_markers = [
                "задача не решена",
                "решение не найдено",
                "не удалось найти решение",
                "изменить задачу",
                "переформулировать",
                "вернуться к части 1",
            ]
            if any(marker in output_lower for marker in loop_back_markers):
                logger.info(
                    "Step 4.6: Task not solved, "
                    "recommending loop back to 1.1"
                )
                return "1.1"

        return None

    def can_complete_early(
        self, step_code: str, llm_output: str
    ) -> bool:
        """
        Check if the session can be completed early at the current step.

        Step 1.7 checks standards applicability. If a standard directly
        solves the task, the session may optionally end early (though
        in full ARIZ we typically continue for thoroughness).

        Args:
            step_code: The current step code.
            llm_output: The LLM output for this step.

        Returns:
            True if early completion is possible.
        """
        if step_code == "1.7":
            output_lower = llm_output.lower()
            early_markers = [
                "задача решена стандартом",
                "стандарт полностью решает",
                "решение найдено через стандарт",
            ]
            return any(m in output_lower for m in early_markers)

        return False

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------

    def build_session_summary(self, session: ARIZSession) -> dict[str, Any]:
        """
        Build a comprehensive session summary for reports and display.

        Groups step results by part, includes all extracted entities,
        context snapshot, and progress information.

        Args:
            session: The ARIZ session to summarize.

        Returns:
            Dict with full session data organized by parts.
        """
        problem = session.problem

        # Collect step results grouped by part
        parts_data: dict[int, list[dict[str, Any]]] = {
            1: [], 2: [], 3: [], 4: [],
        }
        completed_codes: set[str] = set()

        for sr in session.steps.order_by("created_at"):
            part = self.get_part_for_step(sr.step_code)
            parts_data.setdefault(part, []).append({
                "code": sr.step_code,
                "name": sr.step_name,
                "status": sr.status,
                "user_input": sr.user_input,
                "result": sr.validated_result or sr.llm_output,
                "validation_notes": sr.validation_notes,
            })
            if sr.status == "completed":
                completed_codes.add(sr.step_code)

        # Contradictions
        contradictions = [
            {
                "type": c.type,
                "quality_a": c.quality_a,
                "quality_b": c.quality_b,
                "property_s": c.property_s,
                "anti_property_s": c.anti_property_s,
                "formulation": c.formulation,
            }
            for c in session.contradictions.all()
        ]

        # IKRs
        ikrs = [
            {
                "formulation": ikr.formulation,
                "strengthened_formulation": ikr.strengthened_formulation,
                "vpr_used": ikr.vpr_used,
            }
            for ikr in session.ikrs.all()
        ]

        # Solutions
        solutions = [
            {
                "title": sol.title,
                "description": sol.description,
                "method_used": sol.method_used,
                "novelty_score": sol.novelty_score,
                "feasibility_score": sol.feasibility_score,
            }
            for sol in session.solutions.order_by("-novelty_score")
        ]

        # Progress
        progress = self.get_full_progress(completed_codes)

        return {
            "session_id": session.pk,
            "mode": self.MODE_NAME,
            "status": session.status,
            "problem": {
                "id": problem.pk,
                "title": problem.title,
                "description": problem.original_description,
                "domain": problem.domain,
            },
            "progress": progress,
            "parts": {
                part_num: {
                    "name": self.get_part_name(part_num),
                    "description": self.get_part_description(part_num),
                    "steps": steps,
                }
                for part_num, steps in parts_data.items()
            },
            "contradictions": contradictions,
            "ikrs": ikrs,
            "solutions": solutions,
            "context_snapshot": session.context_snapshot,
        }
