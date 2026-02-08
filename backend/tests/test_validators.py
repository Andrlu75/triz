"""
Tests for ARIZ validators — rule-based checks for step outputs.

Each validator is tested with valid input, invalid input, and edge cases.
"""
import pytest

from apps.ariz_engine.validators.base import (
    VALIDATORS,
    BaseValidator,
    ConflictAmplificationValidator,
    ContradictionValidator,
    FalsenessValidator,
    FunctionValidator,
    IKRValidator,
    TermsValidator,
    ValidationResult,
    get_validator,
    get_validators_for_step,
    validate_step_output,
)


# ---------------------------------------------------------------------------
# ValidationResult dataclass tests
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_creation_defaults(self):
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.notes == []
        assert result.suggestions == []
        assert result.validator_name == ""

    def test_creation_with_all_fields(self):
        result = ValidationResult(
            is_valid=False,
            notes=["Issue 1", "Issue 2"],
            suggestions=["Fix it"],
            validator_name="test_validator",
        )
        assert result.is_valid is False
        assert len(result.notes) == 2
        assert len(result.suggestions) == 1
        assert result.validator_name == "test_validator"

    def test_to_dict(self):
        result = ValidationResult(
            is_valid=True,
            notes=["note"],
            suggestions=["suggestion"],
            validator_name="my_validator",
        )
        d = result.to_dict()
        assert d["valid"] is True
        assert d["validator"] == "my_validator"
        assert d["issues"] == ["note"]
        assert d["suggestions"] == ["suggestion"]

    def test_to_dict_empty(self):
        result = ValidationResult(is_valid=False)
        d = result.to_dict()
        assert d["valid"] is False
        assert d["validator"] == ""
        assert d["issues"] == []
        assert d["suggestions"] == []


# ---------------------------------------------------------------------------
# FalsenessValidator tests
# ---------------------------------------------------------------------------


class TestFalsenessValidator:
    @pytest.fixture()
    def validator(self):
        return FalsenessValidator()

    def test_valid_problem(self, validator):
        content = (
            "Трубопровод нагревается при транспортировке горячей жидкости. "
            "Необходимо обеспечить охлаждение, не увеличивая стоимость системы "
            "и не снижая производительность."
        )
        result = validator.validate(content)
        assert result["valid"] is True
        assert result["issues"] == []

    def test_too_short(self, validator):
        result = validator.validate("Проблема с нагревом")
        assert result["valid"] is False
        assert any("слишком короткая" in issue for issue in result["issues"])

    def test_falseness_indicator_simple_solution(self, validator):
        content = (
            "Данная задача имеет простое решение, которое можно найти "
            "в любом справочнике по теплообмену. Нужно просто добавить изоляцию."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("простое решение" in issue for issue in result["issues"])

    def test_falseness_indicator_already_solved(self, validator):
        content = (
            "Эта задача уже решена на практике, и решение хорошо известно "
            "инженерам-теплотехникам. Стандартный подход работает."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("уже решена" in issue for issue in result["issues"])

    def test_falseness_indicator_obvious(self, validator):
        content = (
            "Очевидно, что нужно просто увеличить диаметр трубы. "
            "Это очевидно из расчётов и не требует творческого подхода."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("очевидно" in issue for issue in result["issues"])

    def test_falseness_indicator_does_not_exist(self, validator):
        content = (
            "Проблема на самом деле не существует. Система работает в пределах "
            "штатных параметров, и перегрев — это нормальный режим работы."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("не существует" in issue for issue in result["issues"])

    def test_falseness_indicator_trivial(self, validator):
        content = (
            "Решение тривиально — достаточно заменить материал трубопровода "
            "на более теплостойкий вариант, доступный в каталоге."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("тривиально" in issue for issue in result["issues"])

    def test_falseness_indicator_standard_solution(self, validator):
        content = (
            "Для данной задачи существует стандартное решение. "
            "Достаточно установить радиатор по инженерным рекомендациям."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("стандартное решение" in issue for issue in result["issues"])

    def test_multiple_issues(self, validator):
        content = "Тривиально"
        result = validator.validate(content)
        assert result["valid"] is False
        # Should have both "too short" and "trivial" issues
        assert len(result["issues"]) >= 2

    def test_has_suggestions_on_failure(self, validator):
        result = validator.validate("Простое решение для нагрева трубопровода")
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0

    def test_validator_name(self, validator):
        result = validator.validate("Короткая")
        assert result["validator"] == "falseness_check"

    def test_case_insensitive(self, validator):
        content = (
            "Это ТРИВИАЛЬНО и является стандартным подходом, "
            "не требующим никакого анализа по методологии."
        )
        result = validator.validate(content)
        assert result["valid"] is False

    def test_empty_string(self, validator):
        result = validator.validate("")
        assert result["valid"] is False
        assert any("слишком короткая" in issue for issue in result["issues"])

    def test_exactly_50_chars(self, validator):
        # 50 chars should pass the length check (need 50+)
        content = "A" * 50
        result = validator.validate(content)
        # Should be valid if no falseness indicators
        assert result["valid"] is True

    def test_49_chars_fails(self, validator):
        content = "A" * 49
        result = validator.validate(content)
        assert result["valid"] is False

    def test_whitespace_only(self, validator):
        result = validator.validate("   \t\n   ")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# TermsValidator tests
# ---------------------------------------------------------------------------


class TestTermsValidator:
    @pytest.fixture()
    def validator(self):
        return TermsValidator()

    def test_valid_no_terms_b2c(self, validator):
        content = (
            "Трубопровод должен быть горячим для транспортировки, "
            "но при этом не должен нагревать окружающие элементы."
        )
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is True

    def test_b2b_allows_terms(self, validator):
        content = "Используем вепольный анализ для ИКР и определим ОП."
        result = validator.validate(content, context={"audience": "b2b"})
        assert result["valid"] is True

    def test_b2c_detects_vepol(self, validator):
        content = (
            "Используем вепольный анализ для определения противоречия. "
            "Затем сформулируем идеальный результат."
        )
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False
        issues_text = " ".join(result["issues"])
        assert "вепольный" in issues_text.lower()

    def test_b2c_detects_ikr(self, validator):
        content = "Для определения ИКР необходимо учитывать все факторы системы."
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False

    def test_default_audience_is_b2c(self, validator):
        content = "Применим метод ММЧ для решения задачи и построения модели."
        result = validator.validate(content)  # no context
        assert result["valid"] is False

    def test_multiple_terms_detected(self, validator):
        content = "Веполь и суперсистема используются для формулировки результата."
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False

    def test_suggestions_for_terms(self, validator):
        content = "Веполь и суперсистема необходимы для анализа системы."
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
        assert any("Замените" in s for s in result["suggestions"])

    def test_no_terms_in_content(self, validator):
        content = (
            "Деталь нагревается при обработке. Нужно найти способ "
            "охладить деталь, не замедляя процесс обработки."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_case_insensitive_term_detection(self, validator):
        content = "Нужно провести ВЕПОЛЬНЫЙ анализ системы для решения."
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False

    def test_validator_name(self, validator):
        result = validator.validate("test content")
        assert result["validator"] == "terms_check"

    def test_empty_context(self, validator):
        content = "Определим ТП в системе для анализа противоречий."
        result = validator.validate(content, context={})
        assert result["valid"] is False

    def test_none_context(self, validator):
        content = "Определим ТП в системе для анализа противоречий."
        result = validator.validate(content, context=None)
        assert result["valid"] is False

    def test_each_term_individually(self, validator):
        for term in TermsValidator.TRIZ_TERMS:
            content = f"Для анализа используем {term} как основной инструмент."
            result = validator.validate(content, context={"audience": "b2c"})
            assert result["valid"] is False, f"Term '{term}' should be detected"

    def test_max_5_suggestions(self, validator):
        # Even with many terms, suggestions should be limited
        content = (
            "Веполь, моносистема, бисистема, антисистема, "
            "суперсистема, полисистема, оператор РВС для анализа."
        )
        result = validator.validate(content, context={"audience": "b2c"})
        assert result["valid"] is False
        assert len(result["suggestions"]) <= 5


# ---------------------------------------------------------------------------
# ContradictionValidator tests
# ---------------------------------------------------------------------------


class TestContradictionValidator:
    @pytest.fixture()
    def validator(self):
        return ContradictionValidator()

    def test_valid_contradiction_but_at_the_same_time(self, validator):
        content = (
            "Деталь должна быть прочной, чтобы выдерживать нагрузку, "
            "но при этом должна быть лёгкой для транспортировки."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_with_on_one_hand_on_other(self, validator):
        content = (
            "С одной стороны, покрытие должно быть толстым для защиты. "
            "С другой стороны, оно должно быть тонким для теплоотвода."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_with_must_must_not(self, validator):
        content = (
            "Трубка должен быть широкой, чтобы пропускать больше жидкости, "
            "и не должен быть широкой, чтобы занимать мало места."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_with_however(self, validator):
        content = (
            "Необходимо увеличить скорость вращения, однако при увеличении "
            "скорости возникают вибрации и повышенный износ подшипников."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_with_increase_decrease(self, validator):
        content = (
            "Если увеличить давление в системе, то повысится производительность, "
            "но если уменьшить давление, то снизится износ уплотнений."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_with_necessary_impossible(self, validator):
        content = (
            "Необходимо обеспечить герметичность соединения, но это "
            "невозможно при текущей конструкции фланца."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_invalid_no_opposition(self, validator):
        content = (
            "Деталь нагревается при работе. Нужно найти способ "
            "снизить температуру детали. Рассмотрим варианты охлаждения."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("явного противоречия" in issue for issue in result["issues"])

    def test_invalid_too_short(self, validator):
        result = validator.validate("Короткая формулировка.")
        assert result["valid"] is False
        assert any("слишком короткая" in issue for issue in result["issues"])

    def test_both_issues_short_and_no_opposition(self, validator):
        result = validator.validate("Просто текст")
        assert result["valid"] is False
        assert len(result["issues"]) >= 2

    def test_has_suggestions(self, validator):
        result = validator.validate(
            "Нет противоречия в этом длинном тексте для тестирования валидатора."
        )
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
        assert any("Элемент X" in s for s in result["suggestions"])

    def test_validator_name(self, validator):
        result = validator.validate("test")
        assert result["validator"] == "contradiction_check"

    def test_each_marker_individually(self, validator):
        for marker in ContradictionValidator.CONTRADICTION_MARKERS:
            content = f"В данной системе {marker} возникает проблема совместимости."
            result = validator.validate(content)
            assert result["valid"] is True, f"Marker '{marker}' should make validation pass"


# ---------------------------------------------------------------------------
# ConflictAmplificationValidator tests
# ---------------------------------------------------------------------------


class TestConflictAmplificationValidator:
    @pytest.fixture()
    def validator(self):
        return ConflictAmplificationValidator()

    def test_valid_absolutely(self, validator):
        content = (
            "Температура должна быть абсолютно максимальной для плавления, "
            "и при этом абсолютно минимальной для сохранения формы."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_completely(self, validator):
        content = "Элемент должен быть полностью прозрачным и одновременно непрозрачным."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ideally(self, validator):
        content = "Идеально, если элемент сам выполняет функцию без внешнего воздействия."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_limit_and_zero(self, validator):
        content = (
            "Прочность должна быть предельно высокой, а вес — "
            "нулевой. Элемент бесконечно тонкий и бесконечно прочный."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_maximally(self, validator):
        content = "Деталь максимально жёсткая и одновременно гибкая."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_invalid_no_amplification(self, validator):
        content = (
            "Деталь должна быть прочной и лёгкой одновременно. "
            "Нужно найти компромисс между прочностью и весом."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("не доведено до предела" in issue for issue in result["issues"])

    def test_has_two_suggestions(self, validator):
        content = "Нужно увеличить прочность и уменьшить вес детали."
        result = validator.validate(content)
        assert result["valid"] is False
        assert len(result["suggestions"]) == 2

    def test_case_insensitive(self, validator):
        content = "Элемент АБСОЛЮТНО должен выдерживать нагрузку."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_validator_name(self, validator):
        result = validator.validate("test")
        assert result["validator"] == "conflict_check"

    def test_each_marker_individually(self, validator):
        for marker in ConflictAmplificationValidator.AMPLIFICATION_MARKERS:
            content = f"Противоречие: элемент {marker} должен быть и не должен быть."
            result = validator.validate(content)
            assert result["valid"] is True, f"Marker '{marker}' should make validation pass"


# ---------------------------------------------------------------------------
# FunctionValidator tests
# ---------------------------------------------------------------------------


class TestFunctionValidator:
    @pytest.fixture()
    def validator(self):
        return FunctionValidator()

    def test_valid_processes(self, validator):
        content = "Резец обрабатывает заготовку, удаляя слой металла."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_heats(self, validator):
        content = "Нагреватель нагревает жидкость до требуемой температуры."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_protects(self, validator):
        content = "Покрытие защищает поверхность от коррозии и механических повреждений."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_connects(self, validator):
        content = "Клей соединяет две поверхности, обеспечивая герметичность."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_cools(self, validator):
        content = "Вентилятор охлаждает процессор, отводя тепло через радиатор."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_moves(self, validator):
        content = "Конвейер перемещает заготовки между станциями обработки."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_holds(self, validator):
        content = "Зажим удерживает деталь в нужном положении при обработке."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_separates(self, validator):
        content = "Фильтр разделяет жидкость на чистую и загрязнённую фракции."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_measures(self, validator):
        content = "Датчик измеряет температуру жидкости в режиме реального времени."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_transmits(self, validator):
        content = "Привод передаёт вращение от двигателя к рабочему органу."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_transforms(self, validator):
        content = "Трансформатор преобразует напряжение из высокого в низкое."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_destroys(self, validator):
        content = "Дробилка разрушает крупные куски породы до мелкой фракции."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_invalid_no_action(self, validator):
        content = "Устройство работает в системе для обеспечения результата."
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("явного действия" in issue for issue in result["issues"])

    def test_invalid_too_short(self, validator):
        result = validator.validate("Резец режет")
        assert result["valid"] is False
        assert any("слишком короткая" in issue for issue in result["issues"])

    def test_both_issues(self, validator):
        result = validator.validate("Работа")
        assert result["valid"] is False
        assert len(result["issues"]) >= 2

    def test_has_suggestions(self, validator):
        result = validator.validate("Устройство функционирует в рамках системы.")
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
        assert any("Инструмент" in s for s in result["suggestions"])

    def test_validator_name(self, validator):
        result = validator.validate("test")
        assert result["validator"] == "function_check"


# ---------------------------------------------------------------------------
# IKRValidator tests
# ---------------------------------------------------------------------------


class TestIKRValidator:
    @pytest.fixture()
    def validator(self):
        return IKRValidator()

    def test_valid_ikr_samo(self, validator):
        content = (
            "Покрытие само защищает поверхность от коррозии, "
            "не требуя дополнительного обслуживания."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ikr_automatically(self, validator):
        content = (
            "Система автоматически регулирует температуру, "
            "поддерживая оптимальный режим без вмешательства оператора."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ikr_without(self, validator):
        content = (
            "Деталь выдерживает нагрузку без дополнительных "
            "усилений и без увеличения веса конструкции."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ikr_ideally(self, validator):
        content = (
            "Идеально, если трубопровод сам регулирует свою температуру, "
            "обеспечивая нужный режим работы."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ikr_ne_trebuet(self, validator):
        content = (
            "Устройство не требует внешнего источника энергии "
            "и выполняет свою функцию за счёт внутренних ресурсов."
        )
        result = validator.validate(content)
        assert result["valid"] is True

    def test_valid_ikr_selfstanding(self, validator):
        content = "Элемент самостоятельно выполняет все необходимые функции."
        result = validator.validate(content)
        assert result["valid"] is True

    def test_invalid_no_ideal_markers(self, validator):
        content = (
            "Нужно изменить конструкцию трубопровода. "
            "Добавить теплоизоляцию и систему охлаждения."
        )
        result = validator.validate(content)
        assert result["valid"] is False
        assert any("идеальность" in issue for issue in result["issues"])

    def test_invalid_too_short(self, validator):
        result = validator.validate("Элемент сам делает")
        assert result["valid"] is False
        assert any("слишком короткая" in issue for issue in result["issues"])

    def test_both_issues(self, validator):
        result = validator.validate("Нужно изменить")
        assert result["valid"] is False
        assert len(result["issues"]) >= 2

    def test_has_suggestions(self, validator):
        result = validator.validate(
            "Изменить конструкцию для лучшего охлаждения трубопровода."
        )
        assert result["valid"] is False
        assert len(result["suggestions"]) > 0
        assert any("X-элемент" in s for s in result["suggestions"])

    def test_validator_name(self, validator):
        result = validator.validate("test")
        assert result["validator"] == "ikr_check"

    def test_each_marker_individually(self, validator):
        for marker in IKRValidator.IKR_MARKERS:
            content = (
                f"Элемент {marker} выполняет функцию и обеспечивает нужный результат."
            )
            result = validator.validate(content)
            assert result["valid"] is True, (
                f"Marker '{marker}' should make IKR validation pass"
            )


# ---------------------------------------------------------------------------
# Validator registry tests
# ---------------------------------------------------------------------------


class TestValidatorRegistry:
    def test_get_validator_falseness(self):
        v = get_validator("falseness_check")
        assert v is not None
        assert isinstance(v, FalsenessValidator)

    def test_get_validator_terms(self):
        v = get_validator("terms_check")
        assert v is not None
        assert isinstance(v, TermsValidator)

    def test_get_validator_contradiction(self):
        v = get_validator("contradiction_check")
        assert v is not None
        assert isinstance(v, ContradictionValidator)

    def test_get_validator_conflict(self):
        v = get_validator("conflict_check")
        assert v is not None
        assert isinstance(v, ConflictAmplificationValidator)

    def test_get_validator_function(self):
        v = get_validator("function_check")
        assert v is not None
        assert isinstance(v, FunctionValidator)

    def test_get_validator_ikr(self):
        v = get_validator("ikr_check")
        assert v is not None
        assert isinstance(v, IKRValidator)

    def test_get_validator_unknown(self):
        v = get_validator("nonexistent")
        assert v is None

    def test_all_validators_registered(self):
        expected = [
            "falseness_check", "terms_check", "contradiction_check",
            "conflict_check", "function_check", "ikr_check",
        ]
        for name in expected:
            assert get_validator(name) is not None, f"Validator '{name}' not registered"

    def test_all_validators_have_name(self):
        for name, validator in VALIDATORS.items():
            assert validator.name == name
            assert isinstance(validator.rules, list)
            assert len(validator.rules) > 0

    def test_all_validators_are_base_subclass(self):
        for name, validator in VALIDATORS.items():
            assert isinstance(validator, BaseValidator)


# ---------------------------------------------------------------------------
# get_validators_for_step tests
# ---------------------------------------------------------------------------


class TestGetValidatorsForStep:
    def test_single_validator(self):
        validators = get_validators_for_step(["falseness_check"])
        assert len(validators) == 1
        assert isinstance(validators[0], FalsenessValidator)

    def test_multiple_validators(self):
        validators = get_validators_for_step(["falseness_check", "terms_check"])
        assert len(validators) == 2
        assert isinstance(validators[0], FalsenessValidator)
        assert isinstance(validators[1], TermsValidator)

    def test_skips_unknown(self):
        validators = get_validators_for_step(
            ["falseness_check", "nonexistent", "ikr_check"]
        )
        assert len(validators) == 2

    def test_empty_list(self):
        validators = get_validators_for_step([])
        assert validators == []

    def test_all_unknown(self):
        validators = get_validators_for_step(["unknown1", "unknown2"])
        assert validators == []


# ---------------------------------------------------------------------------
# validate_step_output tests
# ---------------------------------------------------------------------------


class TestValidateStepOutput:
    def test_single_validator(self):
        results = validate_step_output(
            ["falseness_check"],
            "Трубопровод нагревается при транспортировке горячей жидкости "
            "и вызывает повреждения окружающих конструкций.",
        )
        assert len(results) == 1
        assert results[0]["validator"] == "falseness_check"

    def test_multiple_validators(self):
        results = validate_step_output(
            ["falseness_check", "terms_check"],
            "Трубопровод нагревается при транспортировке горячей жидкости "
            "и вызывает повреждения окружающих конструкций.",
        )
        assert len(results) == 2
        assert results[0]["validator"] == "falseness_check"
        assert results[1]["validator"] == "terms_check"

    def test_skips_unknown(self):
        results = validate_step_output(
            ["falseness_check", "nonexistent"],
            "Трубопровод нагревается при транспортировке горячей жидкости "
            "и вызывает повреждения.",
        )
        assert len(results) == 1

    def test_empty_list(self):
        results = validate_step_output([], "Any content")
        assert results == []

    def test_with_context(self):
        results = validate_step_output(
            ["terms_check"],
            "Используем вепольный анализ.",
            context={"audience": "b2b"},
        )
        assert len(results) == 1
        assert results[0]["valid"] is True

    def test_all_results_have_expected_keys(self):
        results = validate_step_output(
            ["falseness_check", "terms_check", "contradiction_check"],
            "Если увеличить скорость, качество падает, но при этом "
            "производительность растёт. Нужно найти баланс для системы.",
        )
        for r in results:
            assert "valid" in r
            assert "validator" in r
            assert "issues" in r
            assert "suggestions" in r
