from django.urls import path
from .views import (
    register_view, login_view, logout_view, profile_view, 
    forgot_password_view, verify_forgot_password_otp_view, reset_password_view
)

app_name = "accounts"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("forgot-password/", forgot_password_view, name="forgot-password"),
    path("forgot-password/verify/", verify_forgot_password_otp_view, name="verify-forgot-otp"),
    path("forgot-password/reset/", reset_password_view, name="reset-password"),
]