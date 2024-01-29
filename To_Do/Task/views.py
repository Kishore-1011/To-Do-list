from django.shortcuts import render, redirect
from .forms import CreateUserForm, LoginForm
from django.contrib.auth.models import auth
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from .models import Task
from django.contrib import messages
from .forms import CreateTaskForm,UpdateTaskForm
# - Homepage 

def home(request):
    return render(request, 'Task/index.html')


# - Register a user

def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account was created successfully')
            return redirect("my-login")
    context = {'form':form}
    return render(request, 'Task/register.html', context=context)


# - Login a user

def my_login(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect("dashboard")
    context = {'form':form}
    return render(request, 'Task/my-login.html', context=context)


# - Dashboard

@login_required(login_url='my-login')
def dashboard(request):
    my_task = Task.objects.all()
    context = {'records':my_task}
    return render(request, 'Task/dashboard.html', context = context)

# create task
@login_required(login_url='my-login')
def create_task(request):
    form = CreateTaskForm()
    if request.method == 'POST':
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was created successfully')
            return redirect("dashboard")
    context = {'form':form}
    return render(request, 'Task/create_task.html', context = context)


#upadte task
@login_required(login_url='my-login')
def update_task(request,pk):
    task = Task.objects.get(id=pk)
    form = UpdateTaskForm(instance=task)
    if request.method == 'POST':
        form = UpdateTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task was updated successfully')
            return redirect("dashboard")
    context = {'form':form}
    return render(request, 'Task/update_task.html', context = context)


# delete task
@login_required(login_url='my-login')
def delete_task(request,pk):
    task = Task.objects.get(id=pk)
    task.delete()
    messages.success(request, 'Task was deleted successfully')
    return redirect('dashboard')


def user_logout(request):
    auth.logout(request)
    messages.success(request, 'loged out successfully')
    return redirect("my-login")
