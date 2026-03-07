"""Contains choices for tutorials app."""

from django.db import models


class RoleChoice(models.TextChoices):
    STUDENT = "student", "STUDENT"
    TEACHER = "teacher", "TEACHER"


class MaterialChoice(models.TextChoices):
    NOTE = "note", "NOTE"
    WORKSHEET = "worksheet", "WORKSHEET"
    QUESTION_PAPER = "question_paper", "QUESTION_PAPER"
