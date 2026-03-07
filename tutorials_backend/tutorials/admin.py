from django.contrib import admin
from .models import Profile, Material, StudentSubmission, TeacherStudent


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "full_name", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "full_name", "display_name")


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "material_type", "uploaded_by", "accepts_submissions", "created_at")
    list_filter = ("material_type", "accepts_submissions")
    search_fields = ("title", "description")


@admin.register(TeacherStudent)
class TeacherStudentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "student", "created_at")
    list_filter = ("teacher",)
    search_fields = ("teacher__full_name", "student__full_name")


@admin.register(StudentSubmission)
class StudentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("material", "student", "submitted_at", "note")
    list_filter = ("material__material_type",)
    search_fields = ("student__full_name", "material__title")
