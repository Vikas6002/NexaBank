from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .services import create_otp, verify_otp

User = get_user_model()


@login_required
def send_otp_view(request):
    try:
        create_otp(request.user)
        messages.success(request, "OTP sent to your email.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect("verify-otp")


@login_required
def verify_otp_view(request):
    if request.method == "POST":
        code = request.POST.get("otp")

        success, message = verify_otp(request.user, code)

        if success:
            messages.success(request, message)
            return redirect("accounts:profile")

        else:
            messages.error(request, message)

    return render(request, "otp/verify_otp.html")


@login_required
def resend_otp_view(request):
    try:
        create_otp(request.user)
        messages.success(request, "OTP resent successfully.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect("otp:verify-otp")