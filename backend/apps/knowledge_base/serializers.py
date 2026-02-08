"""
DRF serializers for TRIZ Knowledge Base API.
"""
from rest_framework import serializers

from apps.knowledge_base.models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)


class TRIZPrincipleListSerializer(serializers.ModelSerializer):
    """Compact serializer for principle list views."""

    class Meta:
        model = TRIZPrinciple
        fields = [
            "id",
            "number",
            "name",
            "is_additional",
        ]


class TRIZPrincipleDetailSerializer(serializers.ModelSerializer):
    """Full serializer for principle detail views."""

    paired_with_number = serializers.SerializerMethodField()

    class Meta:
        model = TRIZPrinciple
        fields = [
            "id",
            "number",
            "name",
            "description",
            "examples",
            "is_additional",
            "paired_with",
            "paired_with_number",
            "created_at",
            "updated_at",
        ]

    def get_paired_with_number(self, obj: TRIZPrinciple) -> int | None:
        if obj.paired_with:
            return obj.paired_with.number
        return None


class TechnologicalEffectSerializer(serializers.ModelSerializer):
    """Serializer for technological effects."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = TechnologicalEffect
        fields = [
            "id",
            "type",
            "type_display",
            "name",
            "description",
            "function_keywords",
            "distance",
            "created_at",
            "updated_at",
        ]


class StandardSerializer(serializers.ModelSerializer):
    """Serializer for TRIZ standards."""

    class Meta:
        model = Standard
        fields = [
            "id",
            "class_number",
            "number",
            "name",
            "description",
            "applicability",
            "created_at",
            "updated_at",
        ]


class AnalogTaskSerializer(serializers.ModelSerializer):
    """Serializer for analog tasks."""

    distance = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = AnalogTask
        fields = [
            "id",
            "title",
            "problem_description",
            "op_formulation",
            "solution_principle",
            "domain",
            "source",
            "distance",
            "created_at",
            "updated_at",
        ]


class DefinitionSerializer(serializers.ModelSerializer):
    """Serializer for TRIZ definitions."""

    class Meta:
        model = Definition
        fields = [
            "id",
            "number",
            "term",
            "definition",
            "created_at",
            "updated_at",
        ]


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for ARIZ rules."""

    class Meta:
        model = Rule
        fields = [
            "id",
            "number",
            "name",
            "description",
            "examples",
            "created_at",
            "updated_at",
        ]


class TypicalTransformationSerializer(serializers.ModelSerializer):
    """Serializer for typical transformations."""

    class Meta:
        model = TypicalTransformation
        fields = [
            "id",
            "contradiction_type",
            "transformation",
            "description",
            "created_at",
            "updated_at",
        ]


class AnalogSearchQuerySerializer(serializers.Serializer):
    """Serializer for analog task search query parameters."""

    q = serializers.CharField(
        required=True,
        help_text="OP formulation text to search for",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=50,
        help_text="Maximum number of results to return",
    )


class EffectSearchQuerySerializer(serializers.Serializer):
    """Serializer for effect search query parameters."""

    q = serializers.CharField(
        required=True,
        help_text="Function description to search for",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=50,
        help_text="Maximum number of results to return",
    )


class PrincipleSuggestQuerySerializer(serializers.Serializer):
    """Serializer for principle suggestion query parameters."""

    contradiction_type = serializers.ChoiceField(
        choices=["surface", "deepened", "sharpened"],
        required=True,
        help_text="Type of contradiction",
    )
    formulation = serializers.CharField(
        required=False,
        default="",
        help_text="Optional contradiction formulation text",
    )
