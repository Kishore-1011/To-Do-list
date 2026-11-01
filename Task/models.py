from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    Category_Choices = (('H', 'Home'),('S', 'School'),('O', 'Office'),)
    name = models.CharField(max_length=225)
    category = models.CharField(max_length=1, choices=Category_Choices)
    description = models.TextField()
    task_number = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Check if task number needs to be assigned
        if not self.task_number:
            # Get the maximum task number for the current user
            max_task_number = Task.objects.filter(user=self.user).aggregate(models.Max('task_number'))['task_number__max']
            if max_task_number is None:
                max_task_number = 0
            # Assign the next task number
            self.task_number = max_task_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
