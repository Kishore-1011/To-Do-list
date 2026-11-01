from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Task


class BootstrapFormMixin:
    """Adds Bootstrap classes to widgets and marks fields with errors as invalid."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs['class'] = f"{widget.attrs.get('class', '')} is-invalid".strip()
                widget.attrs['aria-invalid'] = 'true'


class CreateUserForm(BootstrapFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': True, 'autocomplete': 'username'})


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class TaskForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'category', 'description']
        labels = {'name': 'Task name'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Submit project report', 'autofocus': True}),
            'description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Add details, links or notes'}),
        }
