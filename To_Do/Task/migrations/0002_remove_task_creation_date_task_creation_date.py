# Generated by Django 5.0 on 2024-01-28 10:03

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Task', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='Creation_date',
        ),
        migrations.AddField(
            model_name='task',
            name='creation_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
