"""
URL configuration for To_Do project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path
import Task.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Task.views.home, name='home'),
    path('register/', Task.views.register, name='register'),
    path('login/', Task.views.my_login, name='my-login'),
    path('logout/', Task.views.user_logout, name='user-logout'),
    path('dashboard/', Task.views.dashboard, name='dashboard'),
    path('board/', Task.views.board, name='board'),
    path('tasks/new/', Task.views.create_task, name='create-task'),
    path('tasks/<int:pk>/edit/', Task.views.update_task, name='update-task'),
    path('tasks/<int:pk>/status/', Task.views.update_status, name='update-status'),
    path('tasks/<int:pk>/complete/', Task.views.toggle_complete, name='toggle-complete'),
    path('tasks/<int:pk>/delete/', Task.views.delete_task, name='delete-task'),
]
