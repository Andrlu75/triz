"""
Tests for ARIZ validators (rule-based checks).
"""
import pytest

from apps.ariz_engine.validators.base import (
    ConflictAmplificationValidator,
    ContradictionValidator,
    FalsenessValidator,
    FunctionValidator,
    IKRValidator,
    TermsValidator,
    get_validator,
    validate_step_output,
)


# ---------------------------------------------------------------------------
# FalsenessValidator
# ---------------------------------------------------------------------------


class TestFalsenessValidator:
    def setup_method(self):
        self.v = FalsenessValidator()

    def test_valid_problem(self):
        result = self.v.validate(
            "Труба перегревается при работе компрессора. "
            "Необходимо обеспечить охлаждение, не увеличивая габариты."
        )
        assert result["valid"] is True

    def test_too_short(self):
        result = self.v.validate("Проблема с трубой.")
        assert result["valid"] is False
        assert any("короткая" in issue for issue in result["issues"])

    def test_falseness_indicator(self):
        result = self.v.validate(
            "Эта задача имеет простое решение. Достаточно увеличить диаметр трубы."
        )
        assert result["valid"] is False
        assert any("ложности" in issue for issue in result["issues"])

    def test_already_solved(self):
        result = self.v.validate(
            "Данная проблема уже решена в предыдущем проекте путём замены материала."
        )
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# TermsValidator
# ---------------------------------------------------------------------------


class TestTermsValidator:
    def setup_method(self):
        self.v = TermsValidator()

    def test_no_terms_b2c(self):
        result = self.v.validate(
            "Нужно найти способ сделать трубу прочнее, не утяжеляя её."
        )
        assert result["valid"] is True

    def test_has_terms_b2c(self):
        result = self.v.validate(
            "Необходимо провести вепольный анализ и определить ИКР."
        )
        assert result["valid"] is False
        assert any("термины" in issue.lower() for issue in result["issues"])

    def test_terms_ok_for_b2b(self):
        result = self.v.validate(
            "Применим оператор РВС и метод ММЧ для решения.",
            context={"audience": "b2b"},
        )
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# ContradictionValidator
# ---------------------------------------------------------------------------


class TestContradictionValidator:
    def setup_method(self):
        self.v = ContradictionValidator()

    def test_valid_contradiction(self):
        result = self.v.validate(
            "Если увеличить температуру обработки, качество повысится, "
            "но при этом возрастёт износ инструмента."
        )
        assert result["valid"] is True

    def test_no_opposition(self):
        result = self.v.validate(
            "Температура обработки влияет на качество продукции."
        )
        assert result["valid"] is False
        assert any("противоречия" in issue for issue in result["issues"])

    def test_too_short(self):
        result = self.v.validate("Противоречие.")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# ConflictAmplificationValidator
# ---------------------------------------------------------------------------


class TestConflictAmplificationValidator:
    def setup_method(self):
        self.v = ConflictAmplificationValidator()

    def test_amplified(self):
        result = self.v.validate(
            "Труба должна быть абсолютно теплопроводной для охлаждения "
            "и полностью теплоизолирующей для защиты."
        )
        assert result["valid"] is True

    def test_not_amplified(self):
        result = self.v.validate(
            "Труба должна быть более теплопроводной и менее проводящей тепло."
        )
        assert result["valid"] is False
        assert any("предела" in issue for issue in result["issues"])


# ---------------------------------------------------------------------------
# FunctionValidator
# ---------------------------------------------------------------------------


class TestFunctionValidator:
    def setup_method(self):
        self.v = FunctionValidator()

    def test_valid_function(self):
        result = self.v.validate(
            "Резец обрабатывает заготовку, удаляя слой металла."
        )
        assert result["valid"] is True

    def test_no_action(self):
        result = self.v.validate(
            "Проблема связана с тем, что система не работает правильно."
        )
        assert result["valid"] is False
        assert any("действия" in issue for issue in result["issues"])

    def test_too_short(self):
        result = self.v.validate("ГФ: резка.")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# IKRValidator
# ---------------------------------------------------------------------------


class TestIKRValidator:
    def setup_method(self):
        self.v = IKRValidator()

    def test_valid_ikr(self):
        result = self.v.validate(
            "Труба сама регулирует температуру, не требуя внешних систем охлаждения."
        )
        assert result["valid"] is True

    def test_no_ideal_marker(self):
        result = self.v.validate(
            "Можно установить систему охлаждения рядом с трубой."
        )
        assert result["valid"] is False
        assert any("идеальность" in issue for issue in result["issues"])

    def test_too_short(self):
        result = self.v.validate("ИКР: труба холодная.")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Registry & batch validation
# ---------------------------------------------------------------------------


class TestValidatorRegistry:
    def test_get_known_validator(self):
        v = get_validator("falseness_check")
        assert v is not None
        assert isinstance(v, FalsenessValidator)

    def test_get_unknown_validator(self):
        v = get_validator("unknown_validator")
        assert v is None

    def test_all_validators_registered(self):
        names = [
            "falseness_check", "terms_check", "contradiction_check",
            "conflict_check", "function_check", "ikr_check",
        ]
        for name in names:
            assert get_validator(name) is not None

    def test_validate_step_output(self):
        results = validate_step_output(
            ["falseness_check", "terms_check"],
            "Труба перегревается при работе компрессора. "
            "Необходимо обеспечить охлаждение, не увеличивая габариты.",
        )
        assert len(results) == 2
        for r in results:
            assert "valid" in r
            assert "issues" in r
