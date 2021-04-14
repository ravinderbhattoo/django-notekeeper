from django.contrib.auth import login, authenticate
from .models import SignUpForm
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('username')
            if name in ['none', 'admin', 'root']:
                messages.error(request, f'Select a different usename. "{name}" is not allowed.')
                return redirect('home')
            else:
                form.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form, 'default': False})

def logout_view(request):
    user = request.user
    logout(request)
    return redirect('login')

def create_default_accounts(request):
    try:
        none_user = User.objects.get(username="none")
        return redirect('home')
    except:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data.get('username')
                if name not in ['none', 'admin', 'root']:
                    messages.error(request, f'Select a different usename. "{name}" is not allowed.')
                    return redirect('home')
                form.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                return redirect('home')
        else:
            form = SignUpForm()
            return render(request, 'signup.html', {'form': form, 'default': True})

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('notes')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })