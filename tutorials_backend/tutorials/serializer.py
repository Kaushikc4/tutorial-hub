from rest_framework import serializers
from django.contrib.auth.models import User
from .choices import RoleChoice
from .models import Profile, Material, StudentSubmission, TeacherStudent


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=("id", "username", "email")


class ProfileSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ("id", "user", "role", "full_name", "display_name", "created_at", "modified_at")
        read_only_fields = ("id", "user", "created_at", "modified_at")


class MaterialSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = (
            "id", "title", "material_type", "description", "file", "file_url",
            "uploaded_by", "uploaded_by_name", "target_students",
            "accepts_submissions", "created_at", "modified_at",
        )
        read_only_fields = ("id", "uploaded_by", "created_at", "modified_at")

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.full_name or obj.uploaded_by.user.username
        return None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    

class MaterialCreateSerializer(serializers.ModelSerializer):
    target_students = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Profile.objects.filter(role=RoleChoice.STUDENT), required=False
    )

    class Meta:
        model = Material
        fields = ("title", "material_type", "description", "file", "accepts_submissions", "target_students")

    def create(self, validated_data):
        target_students = validated_data.pop("target_students", [])
        material = super().create(validated_data)
        if target_students:
            material.target_students.set(target_students)
        return material


class StudentSubmissionSerializer(serializers.ModelSerializer):
    material_title = serializers.CharField(source="material.title", read_only=True)
    material_type = serializers.CharField(source="material.material_type", read_only=True)
    student_name = serializers.SerializerMethodField()
    answer_file_url = serializers.SerializerMethodField()

    class Meta:
        model = StudentSubmission
        fields = (
            "id", "material", "material_title", "material_type", "student", "student_name",
            "answer_file", "answer_file_url", "submitted_at", "note",
        )
        read_only_fields = ("id", "student", "submitted_at")

    def get_student_name(self, obj):
        return obj.student.full_name or obj.student.user.username

    def get_answer_file_url(self, obj):
        if obj.answer_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.answer_file.url)
            return obj.answer_file.url
        return None
    

class StudentSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSubmission
        fields = ("material", "answer_file", "note")