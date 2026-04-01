from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser
from apps.otp.services import create_otp, verify_otp

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.is_verified = False
            user.save()

            # ✅ LOGIN USER HERE
            login(request, user)
            create_otp(user)
            messages.success(request, "Registration successful. Verify OTP.")
            return redirect("otp:send-otp")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.user

            # Log the user in so they can access verify-otp which requires login
            login(request, user)

            if not user.is_verified:
                messages.error(request, "Please verify OTP first")
                return redirect("otp:verify-otp")
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

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            create_otp(user)
            request.session['reset_email'] = email
            messages.success(request, "OTP sent to your email.")
            return redirect("accounts:verify-forgot-otp")
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with that email.")
    
    return render(request, "accounts/forgot_password.html")

def verify_forgot_password_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect("accounts:forgot-password")
        
    if request.method == "POST":
        code = request.POST.get("otp")
        try:
            user = CustomUser.objects.get(email=email)
            success, message = verify_otp(user, code)
            
            if success:
                request.session['can_reset_password'] = True
                messages.success(request, "OTP verified! Please set a new password.")
                return redirect("accounts:reset-password")
            else:
                messages.error(request, message)
        except CustomUser.DoesNotExist:
            return redirect("accounts:forgot-password")
            
    return render(request, "accounts/verify_forgot_password_otp.html", {"email": email})

def reset_password_view(request):
    if not request.session.get('can_reset_password'):
        return redirect("accounts:login")
        
    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        
        if password != confirm:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            email = request.session.get('reset_email')
            try:
                user = CustomUser.objects.get(email=email)
                user.set_password(password)
                user.save()
                
                # Clear session tracking
                if 'reset_email' in request.session:
                    del request.session['reset_email']
                if 'can_reset_password' in request.session:
                    del request.session['can_reset_password']
                
                messages.success(request, "Password reset successfully! Please log in.")
                return redirect("accounts:login")
            except CustomUser.DoesNotExist:
                return redirect("accounts:forgot-password")
            
    return render(request, "accounts/reset_password.html")

