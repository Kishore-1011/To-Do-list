# Generated by Django 5.0 on 2024-01-28 17:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Task', '0004_task_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='user',
        ),
    ]