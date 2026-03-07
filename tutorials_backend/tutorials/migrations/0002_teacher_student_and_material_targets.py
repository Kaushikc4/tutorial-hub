# Generated manually for teacher-student assignment and material target_students

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='tutorials.profile')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_students', to='tutorials.profile')),
            ],
            options={
                'db_table': 'tutorial_teacher_student',
                'unique_together': {('teacher', 'student')},
            },
        ),
        migrations.AddField(
            model_name='material',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='material',
            name='target_students',
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={'role': 'student'},
                related_name='targeted_materials',
                to='tutorials.profile',
            ),
        ),
    ]
