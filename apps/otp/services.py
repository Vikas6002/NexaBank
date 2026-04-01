import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from .models import OTP


OTP_EXPIRY_MINUTES = 5
MAX_OTP_REQUESTS = 3
OTP_REQUEST_WINDOW = 10  # minutes


def generate_otp():
    return str(random.randint(100000, 999999))


def can_request_otp(user):
    """Rate limiting: Max 3 OTPs in 10 mins"""
    window_start = timezone.now() - timedelta(minutes=OTP_REQUEST_WINDOW)

    count = OTP.objects.filter(
        user=user,
        created_at__gte=window_start
    ).count()

    return count < MAX_OTP_REQUESTS


def create_otp(user):
    if not can_request_otp(user):
        raise Exception("Too many OTP requests. Try later.")

    code = generate_otp()
    expiry = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp = OTP.objects.create(
        user=user,
        code=code,
        expiry_time=expiry
    )

    send_otp_email(user.email, code)

    return otp


def send_otp_email(email, code):
    subject = "NexaBank OTP Verification"
    message = f"Your OTP is {code}. It will expire in 5 minutes."

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False
    )


def verify_otp(user, code):
    try:
        otp = OTP.objects.filter(
            user=user,
            is_verified=False
        ).latest("created_at")
    except OTP.DoesNotExist:
        return False, "No OTP found"

    if otp.is_expired():
        return False, "OTP expired"

    if otp.code != code:
        otp.attempts += 1
        otp.save()

        if otp.attempts >= 5:
            return False, "Too many wrong attempts"

        return False, "Invalid OTP"

    otp.is_verified = True
    otp.save()

    # Mark user as verified
    user.is_verified = True
    user.save()

    return True, "OTP verified successfully"

def create_otp(user):
    if not can_request_otp(user):
        raise Exception("Too many OTP requests. Try later.")

    # DELETE OLD OTPs 🔥
    OTP.objects.filter(user=user).delete()

    code = generate_otp()
    expiry = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp = OTP.objects.create(
        user=user,
        code=code,
        expiry_time=expiry
    )

    send_otp_email(user.email, code)

    return otp