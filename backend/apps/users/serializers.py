from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import OrganizationMembership, Organization

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "plan", "locale", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "username", "organization", "role", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class AddMemberSerializer(serializers.Serializer):
    """Validates input for adding a member to an organization."""

    username = serializers.CharField()
    role = serializers.ChoiceField(
        choices=OrganizationMembership.ROLE_CHOICES,
        default="member",
    )
