# Migration: allow longer and optional description

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0002_teacher_student_and_material_targets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='description',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
