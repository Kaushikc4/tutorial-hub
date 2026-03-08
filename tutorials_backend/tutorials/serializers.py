"""DRF serializers for tutorials app."""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile, Material, StudentSubmission

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "role", "full_name", "display_name", "user", "created_at", "modified_at")


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = (
            "id", "title", "material_type", "description", "file",
            "created_at", "accepts_submissions", "uploaded_by",
        )
        read_only_fields = ("uploaded_by",)


class StudentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSubmission
        fields = ("id", "material", "student", "answer_file", "submitted_at", "note")
        read_only_fields = ("student",)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[("student", "student"), ("teacher", "teacher")])
    full_name = serializers.CharField(required=False, allow_blank=True)
    display_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "full_name", "display_name")

    def create(self, validated_data):
        role = validated_data.pop("role")
        full_name = validated_data.pop("full_name", "")
        display_name = validated_data.pop("display_name", "")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.create(user=user, role=role, full_name=full_name, display_name=display_name)
        return user
