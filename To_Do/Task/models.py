from django.utils import timezone
from django.db import models

class Task(models.Model):
    Category_Choices = (('H', 'Home'),('S', 'School'),('O', 'Office'),)
    creation_date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=225)
    category = models.CharField(max_length=1, choices=Category_Choices)
    description = models.TextField()

    def __str__(self):
        return self.name
