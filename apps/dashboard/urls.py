from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('customer/', views.customer_dashboard_view, name='customer'),
    path('teller/', views.teller_dashboard_view, name='teller'),
    path('admin/', views.admin_dashboard_view, name='admin'),
    path('admin/freeze/<int:account_id>/', views.toggle_freeze_account_view, name='toggle-freeze'),
    path('admin/role/<int:user_id>/', views.change_user_role_view, name='change-role'),
    path('admin/approve/<int:transaction_id>/', views.approve_transfer_view, name='approve-transfer'),
]
