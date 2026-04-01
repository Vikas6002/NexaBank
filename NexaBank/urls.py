"""
URL configuration for NexaBank project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='root'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('otp/', include('apps.otp.urls')),
    path('banking/', include('apps.banking.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('statements/', include('apps.statements.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]
