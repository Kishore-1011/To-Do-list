from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['task_number', 'name', 'user', 'category', 'priority', 'status', 'due_date', 'created_at']
    list_display_links = ['task_number', 'name']
    list_filter = ['status', 'priority', 'category', 'due_date']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['task_number', 'created_at', 'completed_at']
    date_hierarchy = 'created_at'
