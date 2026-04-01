from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('customer/', views.customer_dashboard_view, name='customer'),
    path('teller/', views.teller_dashboard_view, name='teller'),
    path('admin/', views.admin_dashboard_view, name='admin'),
]
