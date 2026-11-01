from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CreateUserForm, LoginForm, TaskForm
from .models import Task


# "is_done" keeps completed tasks below open ones for the default sorts
SORT_OPTIONS = {
    'due': ('Due date', ['is_done', F('due_date').asc(nulls_last=True), 'task_number']),
    'priority': ('Priority', ['is_done', '-priority', F('due_date').asc(nulls_last=True), 'task_number']),
    'newest': ('Newest', ['-created_at', '-task_number']),
    'number': ('Task number', ['task_number']),
}


def safe_next(request, default='dashboard'):
    """Return the ?next= / POST next URL if it points back to this site, else the default."""
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                       require_https=request.is_secure()):
        return next_url
    return default


def wants_json(request):
    return request.headers.get('Accept', '').startswith('application/json')


def overdue_filter():
    return Q(due_date__lt=timezone.localdate()) & ~Q(status=Task.Status.COMPLETED)


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

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(safe_next(request))

    context = {'form': form, 'next': safe_next(request, default='')}
    return render(request, 'Task/my-login.html', context=context)


# - Logout (POST only, so a link or image can't sign users out)

@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('my-login')


# - Dashboard (list view with search, filters and sorting)

@login_required
def dashboard(request):
    all_tasks = Task.objects.filter(user=request.user)

    # Summary numbers; order_by() keeps the default ordering out of the GROUP BY
    status_totals = dict(all_tasks.order_by().values_list('status').annotate(total=Count('id')))
    total = sum(status_totals.values())
    completed = status_totals.get(Task.Status.COMPLETED, 0)
    stats = {
        'total': total,
        'open': total - completed,
        'completed': completed,
        'overdue': all_tasks.filter(overdue_filter()).count(),
        'percent_done': round(completed * 100 / total) if total else 0,
    }

    # Filters from the query string
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    priority = request.GET.get('priority', '')
    sort = request.GET.get('sort', 'due')
    if sort not in SORT_OPTIONS:
        sort = 'due'

    tasks = all_tasks
    if query:
        tasks = tasks.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if status == 'open':
        tasks = tasks.exclude(status=Task.Status.COMPLETED)
    elif status == 'overdue':
        tasks = tasks.filter(overdue_filter())
    elif status in Task.Status.values:
        tasks = tasks.filter(status=status)
    if category in dict(Task.Category_Choices):
        tasks = tasks.filter(category=category)
    if priority.isdigit() and int(priority) in Task.Priority.values:
        tasks = tasks.filter(priority=int(priority))
    is_done = Case(When(status=Task.Status.COMPLETED, then=Value(1)), default=Value(0),
                   output_field=IntegerField())
    tasks = tasks.annotate(is_done=is_done).order_by(*SORT_OPTIONS[sort][1])

    context = {
        'records': tasks,
        'stats': stats,
        'query': query,
        'selected_status': status,
        'selected_category': category,
        'selected_priority': priority,
        'selected_sort': sort,
        'is_filtered': bool(query or status or category or priority),
        'status_choices': Task.Status.choices,
        'category_choices': Task.Category_Choices,
        'priority_choices': Task.Priority.choices,
        'sort_choices': [(key, label) for key, (label, _) in SORT_OPTIONS.items()],
    }
    return render(request, 'Task/dashboard.html', context=context)


# - Kanban board

@login_required
def board(request):
    tasks = Task.objects.filter(user=request.user)
    category = request.GET.get('category', '')
    if category in dict(Task.Category_Choices):
        tasks = tasks.filter(category=category)
    tasks = tasks.order_by('-priority', F('due_date').asc(nulls_last=True), 'task_number')

    columns = [
        {'status': value, 'label': label, 'tasks': [t for t in tasks if t.status == value]}
        for value, label in Task.Status.choices
    ]
    context = {
        'columns': columns,
        'selected_category': category,
        'category_choices': Task.Category_Choices,
        'status_choices': Task.Status.choices,
    }
    return render(request, 'Task/board.html', context=context)


# - Create task

@login_required
def create_task(request):
    initial = {}
    if request.GET.get('status') in Task.Status.values:
        initial['status'] = request.GET['status']
    form = TaskForm(initial=initial)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task-{task.task_number} was created.')
            return redirect(safe_next(request))

    context = {'form': form, 'title': 'New task', 'submit_label': 'Create task',
               'next': safe_next(request, default='')}
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
            return redirect(safe_next(request))

    context = {
        'form': form,
        'task': task,
        'title': f'Edit Task-{task.task_number}',
        'submit_label': 'Save changes',
        'next': safe_next(request, default=''),
    }
    return render(request, 'Task/task_form.html', context=context)


# - Change status (Kanban drag and drop, "Move to" menu)

@login_required
@require_POST
def update_status(request, pk):
    task = get_object_or_404(Task, id=pk, user=request.user)
    status = request.POST.get('status', '')
    if status not in Task.Status.values:
        if wants_json(request):
            return JsonResponse({'error': 'Invalid status.'}, status=400)
        messages.error(request, 'That status is not valid.')
        return redirect(safe_next(request))

    task.status = status
    task.save(update_fields=['status', 'completed_at'])
    if wants_json(request):
        return JsonResponse({
            'id': task.id,
            'status': task.status,
            'status_label': task.get_status_display(),
            'due_state': task.due_state,
        })
    messages.success(request, f'Task-{task.task_number} moved to {task.get_status_display()}.')
    return redirect(safe_next(request))


# - Mark complete / reopen

@login_required
@require_POST
def toggle_complete(request, pk):
    task = get_object_or_404(Task, id=pk, user=request.user)
    if task.is_completed:
        task.status = Task.Status.TODO
        messages.success(request, f'Task-{task.task_number} was reopened.')
    else:
        task.status = Task.Status.COMPLETED
        messages.success(request, f'Task-{task.task_number} is complete. Nice work!')
    task.save(update_fields=['status', 'completed_at'])
    return redirect(safe_next(request))


# - Delete task

@login_required
def delete_task(request, pk):
    # Only the owner can delete a task; deleting requires a POST from the confirm page
    task = get_object_or_404(Task, id=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, f'Task-{task.task_number} was deleted.')
        return redirect(safe_next(request))

    context = {'task': task, 'next': safe_next(request, default='')}
    return render(request, 'Task/delete_task.html', context=context)
