from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.is_verified = False  # OTP required
            user.save()

            messages.success(request, "Registration successful. Verify OTP.")
            return redirect('otp:verify')

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.user
            login(request, user)

            messages.success(request, "Login successful")

            # Role-based redirect
            if user.role == 'ADMIN':
                return redirect('dashboard:admin')
            elif user.role == 'TELLER':
                return redirect('dashboard:teller')
            else:
                return redirect('dashboard:customer')

    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('accounts:login')


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    return render(request, "accounts/profile.html", {
        "user": request.user
    })