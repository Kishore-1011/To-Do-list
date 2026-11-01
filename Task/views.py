from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CreateUserForm, LoginForm, TaskForm
from .models import Task


# - Homepage

def home(request):
    return render(request, 'Task/index.html')


# - Register a user

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account is ready.')
            return redirect('dashboard')

    context = {'form': form}
    return render(request, 'Task/register.html', context=context)


# - Login a user

def my_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.POST.get('next') or request.GET.get('next', '')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            # Only follow ?next= if it points back to this site
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('dashboard')

    context = {'form': form, 'next': next_url}
    return render(request, 'Task/my-login.html', context=context)


# - Logout (POST only, so a link or image can't sign users out)

@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('my-login')


# - Dashboard

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user).order_by('task_number')
    # order_by() clears the task_number ordering so it doesn't split the GROUP BY
    counts = dict(tasks.order_by().values_list('category').annotate(total=Count('id')))
    category_counts = [
        {'code': code, 'label': label, 'total': counts.get(code, 0)}
        for code, label in Task.Category_Choices
    ]
    context = {'records': tasks, 'category_counts': category_counts}
    return render(request, 'Task/dashboard.html', context=context)


# - Create task

@login_required
def create_task(request):
    form = TaskForm()
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task-{task.task_number} was created.')
            return redirect('dashboard')

    context = {'form': form, 'title': 'New task', 'submit_label': 'Create task'}
    return render(request, 'Task/task_form.html', context=context)


# - Update task

@login_required
def update_task(request, pk):
    # Only the owner can edit a task; anyone else gets a 404
    task = get_object_or_404(Task, id=pk, user=request.user)
    form = TaskForm(instance=task)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task-{task.task_number} was updated.')
            return redirect('dashboard')

    context = {
        'form': form,
        'task': task,
        'title': f'Edit Task-{task.task_number}',
        'submit_label': 'Save changes',
    }
    return render(request, 'Task/task_form.html', context=context)


# - Delete task

@login_required
def delete_task(request, pk):
    # Only the owner can delete a task; deleting requires a POST from the confirm page
    task = get_object_or_404(Task, id=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, f'Task-{task.task_number} was deleted.')
        return redirect('dashboard')

    context = {'task': task}
    return render(request, 'Task/delete_task.html', context=context)
