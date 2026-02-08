from rest_framework import serializers

from apps.problems.models import Problem, ProblemShare


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "original_description",
            "mode",
            "domain",
            "status",
            "final_report",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "final_report", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ProblemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ["id", "title", "mode", "domain", "status", "created_at", "updated_at"]
        read_only_fields = fields


class ProblemShareSerializer(serializers.ModelSerializer):
    shared_with_username = serializers.CharField(
        source="shared_with.username", read_only=True
    )

    class Meta:
        model = ProblemShare
        fields = [
            "id",
            "problem",
            "shared_with",
            "shared_with_username",
            "permission",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
