"""
ARIZ validators — rule-based checks for step outputs.

Based on the 28 rules of ARIZ-2010 (V. Petrov).
"""
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    notes: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    validator_name: str = ""

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "valid": self.is_valid,
            "validator": self.validator_name,
            "issues": self.notes,
            "suggestions": self.suggestions,
        }


class BaseValidator(ABC):
    """Abstract base class for ARIZ validators."""

    name: str = ""
    rules: list[str] = []

    @abstractmethod
    def validate(self, content: str, context: dict | None = None) -> dict:
        """
        Validate content against ARIZ rules.

        Args:
            content: The LLM output to validate.
            context: Additional context (previous steps, problem, etc.).

        Returns:
            Dict with keys: valid (bool), issues (list[str]), suggestions (list[str]).
        """

    def _result(
        self,
        valid: bool,
        issues: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> dict:
        return {
            "valid": valid,
            "validator": self.name,
            "issues": issues or [],
            "suggestions": suggestions or [],
        }


class FalsenessValidator(BaseValidator):
    """
    Check for false problem formulations (5 points).

    A problem is false if:
    1. It can be solved by known standard methods
    2. The problem is incorrectly formulated
    3. The problem has already been solved
    4. The problem doesn't actually exist
    5. The requirements are contradictory without reason
    """

    name = "falseness_check"
    rules = ["Rule 1: Check for false problems"]

    FALSENESS_INDICATORS = [
        "простое решение",
        "уже решена",
        "не существует",
        "очевидно",
        "тривиально",
        "стандартное решение",
    ]

    def validate(self, content: str, context: dict | None = None) -> dict:
        content_lower = content.lower()
        issues = []

        if len(content.strip()) < 50:
            issues.append("Формулировка задачи слишком короткая (менее 50 символов).")

        for indicator in self.FALSENESS_INDICATORS:
            if indicator in content_lower:
                issues.append(
                    f"Обнаружен индикатор ложности: '{indicator}'. "
                    "Проверьте, не является ли задача ложной."
                )

        if not issues:
            return self._result(True)

        return self._result(
            valid=False,
            issues=issues,
            suggestions=[
                "Переформулируйте задачу, убрав указания на тривиальность.",
                "Убедитесь, что задача не может быть решена стандартными методами.",
            ],
        )


class TermsValidator(BaseValidator):
    """
    Rule 15: Replace special terms with simple descriptions.

    Technical terms should be replaced with descriptions of their
    structure and function.
    """

    name = "terms_check"
    rules = ["Rule 15: Replace special terms"]

    TRIZ_TERMS = [
        "вепольный", "веполь", "полисистема", "моносистема",
        "бисистема", "антисистема", "суперсистема",
        "оператор РВС", "метод ММЧ", "ИКР", "ОП", "УП", "ПП",
        "ГФ", "ТП", "ФП",
    ]

    def validate(self, content: str, context: dict | None = None) -> dict:
        audience = (context or {}).get("audience", "b2c")
        if audience == "b2b":
            return self._result(True)

        content_lower = content.lower()
        found_terms = [
            term for term in self.TRIZ_TERMS
            if term.lower() in content_lower
        ]

        if not found_terms:
            return self._result(True)

        return self._result(
            valid=False,
            issues=[
                f"Обнаружены специальные ТРИЗ-термины: {', '.join(found_terms)}. "
                "В режиме B2C они должны быть заменены простым описанием."
            ],
            suggestions=[
                f"Замените '{term}' описанием его сути простым языком."
                for term in found_terms[:5]
            ],
        )


class ContradictionValidator(BaseValidator):
    """
    Rule 19: Check the formulation of the deepened contradiction (УП).

    The contradiction should clearly state two opposing requirements
    to the same element.
    """

    name = "contradiction_check"
    rules = ["Rule 19: Deepened contradiction formulation"]

    CONTRADICTION_MARKERS = [
        "но при этом", "однако", "с одной стороны", "с другой стороны",
        "если увеличить", "если уменьшить", "должен быть", "не должен быть",
        "необходимо", "невозможно",
    ]

    def validate(self, content: str, context: dict | None = None) -> dict:
        content_lower = content.lower()
        issues = []

        has_opposition = any(
            marker in content_lower for marker in self.CONTRADICTION_MARKERS
        )
        if not has_opposition:
            issues.append(
                "Формулировка не содержит явного противоречия. "
                "Должны быть два противоположных требования к одному элементу."
            )

        if len(content.strip()) < 30:
            issues.append("Формулировка противоречия слишком короткая.")

        if not issues:
            return self._result(True)

        return self._result(
            valid=False,
            issues=issues,
            suggestions=[
                "Используйте формат: 'Элемент X должен быть A, чтобы ..., "
                "и должен быть не-A (или B), чтобы ...'.",
            ],
        )


class ConflictAmplificationValidator(BaseValidator):
    """
    Rules 22-24: Conflict amplification check.

    The sharpened contradiction (ОП) should push the conflict
    to an extreme/limiting state.
    """

    name = "conflict_check"
    rules = ["Rule 22", "Rule 23", "Rule 24"]

    AMPLIFICATION_MARKERS = [
        "абсолютно", "полностью", "максимально", "предельно",
        "бесконечно", "нулевой", "идеально",
    ]

    def validate(self, content: str, context: dict | None = None) -> dict:
        content_lower = content.lower()

        has_amplification = any(
            marker in content_lower for marker in self.AMPLIFICATION_MARKERS
        )

        if has_amplification:
            return self._result(True)

        return self._result(
            valid=False,
            issues=[
                "Обострённое противоречие не доведено до предела. "
                "Конфликт должен быть усилен до предельного состояния."
            ],
            suggestions=[
                "Доведите требования до предельных значений: "
                "'абсолютно', 'полностью', 'максимально'.",
                "Правила 22-24: конфликт должен быть обострён до физического противоречия.",
            ],
        )


class FunctionValidator(BaseValidator):
    """
    Rules 4-11: Check the formulation of the main useful function (ГФ).

    The function should describe the action of an instrument on an object
    in a clear, specific format.
    """

    name = "function_check"
    rules = ["Rules 4-11: Function formulation"]

    def validate(self, content: str, context: dict | None = None) -> dict:
        issues = []

        if len(content.strip()) < 20:
            issues.append("Формулировка функции слишком короткая.")

        content_lower = content.lower()
        action_words = [
            "перемещает", "нагревает", "охлаждает", "удерживает",
            "разделяет", "соединяет", "измеряет", "обрабатывает",
            "передаёт", "преобразует", "защищает", "разрушает",
        ]
        has_action = any(word in content_lower for word in action_words)
        if not has_action:
            issues.append(
                "Формулировка ГФ не содержит явного действия (глагола). "
                "Правила 4-11 требуют указать инструмент и его действие на изделие."
            )

        if not issues:
            return self._result(True)

        return self._result(
            valid=False,
            issues=issues,
            suggestions=[
                "Формат ГФ: '[Инструмент] [действие] [Изделие]'. "
                "Например: 'Резец обрабатывает деталь'.",
            ],
        )


class IKRValidator(BaseValidator):
    """
    Check the Ideal Final Result (IKR) formulation.

    IKR should describe the ideal state where the element
    performs the required function by itself, without complications.
    """

    name = "ikr_check"
    rules = ["IKR formulation check"]

    IKR_MARKERS = [
        "само", "сам", "самостоятельно", "без",
        "не требует", "автоматически", "идеально",
    ]

    def validate(self, content: str, context: dict | None = None) -> dict:
        content_lower = content.lower()
        issues = []

        has_ideal = any(marker in content_lower for marker in self.IKR_MARKERS)
        if not has_ideal:
            issues.append(
                "Формулировка ИКР не содержит указания на идеальность. "
                "ИКР должен описывать, как элемент сам выполняет нужную функцию."
            )

        if len(content.strip()) < 30:
            issues.append("Формулировка ИКР слишком короткая.")

        if not issues:
            return self._result(True)

        return self._result(
            valid=False,
            issues=issues,
            suggestions=[
                "Формат ИКР: '[Элемент/X-элемент] сам [выполняет нужное действие], "
                "не вызывая [нежелательных эффектов]'.",
            ],
        )


# ---------------------------------------------------------------------------
# Validator registry
# ---------------------------------------------------------------------------

VALIDATORS: dict[str, BaseValidator] = {
    "falseness_check": FalsenessValidator(),
    "terms_check": TermsValidator(),
    "contradiction_check": ContradictionValidator(),
    "conflict_check": ConflictAmplificationValidator(),
    "function_check": FunctionValidator(),
    "ikr_check": IKRValidator(),
}


def get_validator(name: str) -> BaseValidator | None:
    """Look up a validator by name."""
    return VALIDATORS.get(name)


def get_validators_for_step(validator_names: list[str]) -> list[BaseValidator]:
    """
    Return validator instances for a list of validator names.

    Args:
        validator_names: List of validator names (e.g. ["falseness_check", "terms_check"]).

    Returns:
        List of BaseValidator instances (unknown names are skipped with a warning).
    """
    validators = []
    for name in validator_names:
        v = get_validator(name)
        if v:
            validators.append(v)
        else:
            logger.warning("Unknown validator requested: %s", name)
    return validators


def validate_step_output(
    validator_names: list[str],
    content: str,
    context: dict | None = None,
) -> list[dict]:
    """
    Run multiple validators on step output.

    Args:
        validator_names: List of validator names to run.
        content: The content to validate.
        context: Additional context.

    Returns:
        List of validation results.
    """
    results = []
    for name in validator_names:
        validator = get_validator(name)
        if validator:
            results.append(validator.validate(content, context))
        else:
            logger.warning("Unknown validator: %s", name)
    return results
