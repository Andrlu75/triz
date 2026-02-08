from rest_framework import serializers

from apps.ariz_engine.models import (
    ARIZSession,
    Contradiction,
    IKR,
    Solution,
    StepResult,
)


class StepResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepResult
        fields = [
            "id",
            "step_code",
            "step_name",
            "user_input",
            "llm_output",
            "validated_result",
            "validation_notes",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class ContradictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contradiction
        fields = [
            "id",
            "type",
            "quality_a",
            "quality_b",
            "property_s",
            "anti_property_s",
            "formulation",
        ]
        read_only_fields = fields


class IKRSerializer(serializers.ModelSerializer):
    class Meta:
        model = IKR
        fields = ["id", "formulation", "strengthened_formulation", "vpr_used"]
        read_only_fields = fields


class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        fields = [
            "id",
            "method_used",
            "title",
            "description",
            "novelty_score",
            "feasibility_score",
            "created_at",
        ]
        read_only_fields = fields


class SessionSerializer(serializers.ModelSerializer):
    steps = StepResultSerializer(many=True, read_only=True)
    contradictions = ContradictionSerializer(many=True, read_only=True)
    ikrs = IKRSerializer(many=True, read_only=True)
    solutions = SolutionSerializer(many=True, read_only=True)

    class Meta:
        model = ARIZSession
        fields = [
            "id",
            "problem",
            "mode",
            "current_step",
            "current_part",
            "status",
            "completed_at",
            "created_at",
            "steps",
            "contradictions",
            "ikrs",
            "solutions",
        ]
        read_only_fields = fields


class SessionListSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)

    class Meta:
        model = ARIZSession
        fields = [
            "id",
            "problem",
            "problem_title",
            "mode",
            "current_step",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class StartSessionSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["express", "full", "autopilot"], default="express")


class SubmitStepSerializer(serializers.Serializer):
    user_input = serializers.CharField(min_length=1)
