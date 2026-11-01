from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Task(models.Model):
    Category_Choices = (('H', 'Home'), ('S', 'School'), ('O', 'Office'),)

    class Status(models.TextChoices):
        TODO = 'todo', 'Yet to start'
        IN_PROGRESS = 'in_progress', 'In progress'
        ON_HOLD = 'on_hold', 'On hold'
        COMPLETED = 'completed', 'Completed'

    class Priority(models.IntegerChoices):
        LOW = 1, 'Low'
        MEDIUM = 2, 'Medium'
        HIGH = 3, 'High'

    # Tasks due within this many days (and not overdue) are flagged "due soon"
    DUE_SOON_DAYS = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=225)
    category = models.CharField(max_length=1, choices=Category_Choices)
    description = models.TextField(blank=True)
    task_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.PositiveSmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        # Check if task number needs to be assigned
        if not self.task_number:
            # Get the maximum task number for the current user
            max_task_number = Task.objects.filter(user=self.user).aggregate(models.Max('task_number'))['task_number__max']
            if max_task_number is None:
                max_task_number = 0
            # Assign the next task number
            self.task_number = max_task_number + 1

        # Record when a task is completed; clear it if the task is reopened
        if self.status == self.Status.COMPLETED:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def due_state(self):
        """'overdue', 'today', 'soon' or '' for open tasks with a due date."""
        if not self.due_date or self.is_completed:
            return ''
        today = timezone.localdate()
        if self.due_date < today:
            return 'overdue'
        if self.due_date == today:
            return 'today'
        if self.due_date <= today + timedelta(days=self.DUE_SOON_DAYS):
            return 'soon'
        return ''

    @property
    def category_style(self):
        # CSS modifier used to colour the category badge
        return {'H': 'home', 'S': 'school', 'O': 'office'}.get(self.category, 'home')

    @property
    def priority_style(self):
        return {1: 'low', 2: 'medium', 3: 'high'}.get(self.priority, 'medium')

    def __str__(self):
        return self.name
