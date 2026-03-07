"""
Tutorial Center models: profiles, materials (notes, worksheets, question papers), submissions.
"""
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from .choices import RoleChoice, MaterialChoice


def material_upload_path(instance, filename):
    """Store by type and date to avoid relying on unsaved instance id."""
    from django.utils import timezone
    folder = instance.__class__.__name__.lower()
    d = timezone.now()
    return os.path.join("tutorial", folder, d.strftime("%Y/%m"), filename)


def submission_upload_path(instance, filename):
    """Store submissions by student and material."""
    return os.path.join(
        "tutorial", "submissions",
        str(instance.student.id),
        str(instance.material.id),
        filename,
    )



class Profile(models.Model):
    """Profile for students and teachers."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutorial_profile"
    )
    role = models.CharField(max_length=10, choices=RoleChoice.choices)
    full_name = models.CharField(max_length=40, blank=True)
    display_name = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tutorial_profile"
    
    def __str__(self):
        return f"{self.role}: {self.full_name or self.user.username}"

    @property
    def is_teacher(self):
        return self.role == RoleChoice.TEACHER
    
    @property
    def is_student(self):
        return self.role == RoleChoice.STUDENT


class TeacherStudent(models.Model):
    """Assignment of a student to a teacher. Only assigned students see that teacher's materials."""
    teacher = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="assigned_students",
    )
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="teachers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tutorial_teacher_student"
        unique_together = [["teacher", "student"]]

    def __str__(self):
        return f"{self.teacher} → {self.student}"


class Material(models.Model):
    """Materials given by the teacher."""
    title = models.CharField(max_length=300)
    material_type = models.CharField(max_length=20, choices=MaterialChoice.choices)
    description = models.CharField(max_length=500, blank=True)
    file = models.FileField(upload_to=material_upload_path, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_materials",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    target_students = models.ManyToManyField(
        Profile,
        related_name="targeted_materials",
        blank=True,
        limit_choices_to={"role": RoleChoice.STUDENT},
    )
    accepts_submissions = models.BooleanField(
        default=True,
        help_text="If True, students can upload answers (e.g. for worksheets/question papers).",
    )

    class Meta:
        db_table = "tutorial_material"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.material_type}: {self.title}"
    
    def save(self, *args, **kwargs):
        if self.material_type == MaterialChoice.NOTE:
            self.accepts_submissions = False
        super().save(*args, **kwargs)


class StudentSubmission(models.Model):
    """A student's uploaded answer (solved paper) for a worksheet or question paper."""
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    answer_file = models.FileField(upload_to=submission_upload_path)
    submitted_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "tutorial_student_submission"
        ordering = ["-submitted_at"]
        unique_together = [["material", "student"]]

    def __str__(self):
        return f"{self.student} → {self.material.title}"
