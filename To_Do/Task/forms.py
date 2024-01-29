# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User 
from .models import Task

from django.forms.widgets import PasswordInput,TextInput

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        # widgets = {
        #     'Username': forms.TextInput(attrs={'class': 'form-control'}),
        #     'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
        #     'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        # }

class LoginForm(AuthenticationForm):
        username = forms.CharField(widget=TextInput())
        password =  forms.CharField(widget=PasswordInput())

#create task
class CreateTaskForm(forms.ModelForm):
     class Meta:
        model = Task
        fields = ['name', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

#update task
class UpdateTaskForm(forms.ModelForm):
     class Meta:
        model = Task
        fields = ['name', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }